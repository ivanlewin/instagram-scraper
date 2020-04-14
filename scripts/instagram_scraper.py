import igram
import json
import os
import pandas as pd
import scraper
from configparser import ConfigParser
from datetime import datetime
from igramscraper import instagram
from pandas.errors import EmptyDataError
from re import match
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from time import sleep, strftime


def load_credentials():

    config_parser = ConfigParser()

    config_parser.read('credentials.txt')
    login_username = config_parser.get('credentials', 'user')
    login_password = config_parser.get('credentials', 'password')
    credentials = (login_username, login_password)

    return credentials


def load_config():

    config_parser = ConfigParser()

    config_parser.read('config.txt')

    scraping_mode = config_parser.get('scraping', 'scraping_mode')

    get_accounts_dict = config_parser.getboolean('dicts', 'get_accounts_dict')
    get_posts_dict = config_parser.getboolean('dicts', 'get_posts_dict')
    number_of_posts = int(config_parser.get('dicts', 'number_of_posts'))

    since = config_parser.get('period', 'since').replace("-", "")
    until = config_parser.get('period', 'until').replace("-", "")

    settings = {
        'get_posts_dict': get_posts_dict,
        'get_accounts_dict': get_accounts_dict,
        'number_of_posts': number_of_posts,
        'scraping_mode': scraping_mode,
        "period_since": since,
        "period_until": until,
    }

    return settings


def load_driver():

    # Find Firefox Profile
    profiles_folder = f"{os.environ['appdata']}\Mozilla\Firefox\Profiles"
    for profile in os.listdir(profiles_folder):
        if "default-release" in profile:
            firefox_profile = webdriver.FirefoxProfile(
                f"{profiles_folder}/{profile}")
            driver = webdriver.Firefox(firefox_profile)

    driver.get('https://www.instagram.com/p/B8o367kgObt/')

    try:
        close_button = driver.find_element_by_css_selector('.xqRnw')
        close_button.click()

    except NoSuchElementException:
        pass

    return driver


def get_comment_info(driver, comment):

    partial_df = pd.DataFrame()

    user = None
    content = None
    like_count = 0
    post_id = None
    conv_id = None
    reply_id = None
    is_reply = False
    comment_date = None

    post_author = driver.find_elements_by_css_selector("a.ZIAjV")[0].text

    user = comment.find_element_by_css_selector('h3 a').text

    content = comment.find_element_by_css_selector('span')
    content = driver.execute_script(
        "return arguments[0].textContent;", content)

    info = comment.find_element_by_css_selector('.aGBdT')

    likes = info.find_element_by_css_selector('div > button:nth-of-type(1)')
    likes = match(r"(\d+)", likes.text)
    if likes:
        like_count = int(likes[0])

    comment_date = info.find_element_by_css_selector(
        'time').get_attribute('datetime')
    m = match(r"(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)T(?P<hour>\d+):(?P<minute>\d+):(?P<second>.\d+)", comment_date)
    comment_date = f"{m['year']}-{m['month']}-{m['day']}-{m['hour']}-{m['minute']}-{m['second']}"
    comment_date = datetime.strptime(comment_date, "%Y-%m-%d-%H-%M-%S")
    comment_date = int(datetime.timestamp(comment_date))

    permalink = info.find_element_by_css_selector(
        '.gU-I7').get_attribute('href')
    m = match(r"https:\/\/www\.instagram\.com\/p\/(?P<post_id>.+)\/c\/(?P<conversation_id>\d+)\/(r\/(?P<reply_id>\d+)\/)?", permalink)
    post_id = m['post_id']
    conv_id = m['conversation_id']
    if m['reply_id']:
        reply_id = m['reply_id']
        is_reply = True

    partial_df["post_author"] = [post_author]
    partial_df["post_id"] = [post_id]
    partial_df["conv_id"] = [conv_id]
    partial_df["reply_id"] = [reply_id]
    partial_df["is_reply"] = [is_reply]
    partial_df["user"] = [user]
    partial_df["comment"] = [content]
    partial_df["like_count"] = [like_count]
    partial_df["timestamp"] = [comment_date]

    return partial_df


def post_scraper(driver, post):

    post_df = pd.DataFrame()

    driver.get(post)
    sleep(2)

    # Load more comments
    try:
        while True:
            load_more_comments = driver.find_element_by_css_selector(
                '.MGdpg > button')
            load_more_comments.click()
            sleep(2)

    except NoSuchElementException:
        pass

    # Load replies to comments
    try:
        view_replies_buttons = driver.find_elements_by_css_selector('.y3zKF')

        for button in view_replies_buttons:
            text = driver.execute_script(
                "return arguments[0].textContent;", button)
            while "Ver" in text or "View" in text:
                button.click()
                sleep(0.5)
                text = driver.execute_script(
                    "return arguments[0].textContent;", button)

    except NoSuchElementException:
        pass

    for comment in driver.find_elements_by_css_selector('ul.Mr508 div.ZyFrc'):

        comment_df = get_comment_info(driver, comment)
        post_df = pd.concat([post_df, comment_df])

    return post_df


def main():

    file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    comments_folder = os.path.relpath("../comments")

    os.chdir(comments_folder)
    print(os.getcwd())

    settings = load_config()
    print(f"Loaded settings at {(strftime('%X %x'))}")

    driver = load_driver()

    if settings["scraping_mode"] == "posts":
        post_list = open("posts.txt", "r").read().splitlines()

        for post in post_list:

            print(f"Post {post_list.index(post)+1} of {len(post_list)}")

            post_df = post_scraper(driver, post)

            try:
                base_df = pd.read_csv(
                    f'{comments_folder}/posts_{file_timestamp}.csv')
            except (FileNotFoundError):
                base_df = pd.DataFrame()

            base_df = pd.concat([base_df, post_df])

            base_df.to_csv(
                f'{comments_folder}/posts_{file_timestamp}.csv', index=False)

    driver.quit()


if __name__ == '__main__':
    main()
