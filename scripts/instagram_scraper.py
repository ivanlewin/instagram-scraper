import os
import pandas as pd
from configparser import ConfigParser
from datetime import datetime
from igramscraper import instagram
from pandas.errors import EmptyDataError
from re import match
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from time import sleep, strftime


def read_credentials():

    config_parser = ConfigParser()

    config_parser.read('credentials.txt')
    login_username = config_parser.get('credentials', 'user')
    login_password = config_parser.get('credentials', 'password')

    return login_username, login_password


def read_config():

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


def scrape_post(driver, post):

    def load_comments():

        # Load all comments
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
            view_replies_buttons = driver.find_elements_by_css_selector(
                '.y3zKF')

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

    def get_comment_info(comment):

        comment_df = pd.DataFrame()

        user = comment.find_element_by_css_selector('h3 a').text

        content = comment.find_element_by_css_selector('.C4VMK span')
        content = driver.execute_script(
            "return arguments[0].textContent;", content)

        info = comment.find_element_by_css_selector('.aGBdT')

        likes = info.find_element_by_css_selector(
            'div > button:nth-of-type(1)')
        m = match(r"(\d+)", likes.text)
        if m:
            like_count = m[0]
        else:
            like_count = 0

        comment_date = info.find_element_by_css_selector(
            'time').get_attribute('datetime')
        m = match(
            r"(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)T(?P<hour>\d+):(?P<minute>\d+):(?P<second>.\d+)(?:\.\d+Z)", comment_date)
        comment_date = f"{m['year']}-{m['month']}-{m['day']}-{m['hour']}-{m['minute']}-{m['second']}"
        comment_date = datetime.strptime(comment_date, "%Y-%m-%d-%H-%M-%S")
        comment_date = datetime.timestamp(comment_date)

        permalink = info.find_element_by_css_selector(
            '.gU-I7').get_attribute('href')
        m = match(
            r"https:\/\/www\.instagram\.com\/p\/(?:.+)\/c\/(?P<c>\d+)\/(r\/(?P<r>\d+)\/)?", permalink)

        if m['r']:
            comment_id = m['r']
            reply_to = m['c']
        else:
            comment_id = m['c']
            reply_to = None

        comment_df["c_id"] = [comment_id]
        comment_df["c_reply_to"] = [reply_to]
        comment_df["c_date"] = [comment_date]
        comment_df["c_user"] = [user]
        comment_df["c_content"] = [content]
        comment_df["c_likes"] = [like_count]
        comment_df["c_permalink"] = [permalink]

        return comment_df

    driver.get(post)
    sleep(2)
    load_comments()

    post_author = driver.find_elements_by_css_selector("a.ZIAjV")[0].text

    post_likes = driver.find_element_by_css_selector(".Nm9Fw span").text
    post_likes = post_likes.replace(",", "")

    post_info = driver.find_element_by_css_selector(".c-Yi7")

    post_id = post_info.get_attribute('href')
    m = match(r"https:\/\/www\.instagram\.com\/p\/(?P<post_id>.+)\/", post_id)
    post_id = m['post_id']

    post_created_at = post_info.find_element_by_css_selector(
        "._1o9PC").get_attribute('datetime')
    m = match(r"(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)T(?P<hour>\d+):(?P<minute>\d+):(?P<second>.\d+)(?:\.\d+Z)", post_created_at)
    post_created_at = f"{m['year']}-{m['month']}-{m['day']}-{m['hour']}-{m['minute']}-{m['second']}"
    post_created_at = datetime.strptime(post_created_at, "%Y-%m-%d-%H-%M-%S")
    post_created_at = datetime.timestamp(post_created_at)

    post_df = pd.DataFrame()

    for comment in driver.find_elements_by_css_selector('ul.Mr508 div.ZyFrc'):

        comment_df = get_comment_info(comment)
        post_df = pd.concat([post_df, comment_df])

    post_df["p_id"] = post_id
    post_df["p_author"] = post_author
    post_df["p_date"] = post_created_at
    post_df["p_likes"] = post_likes
    post_df["p_comments"] = len(post_df.index)

    # Reorder columns with post info first
    new_order = list(
        post_df.columns.values[7:]) + list(post_df.columns.values[:7])
    post_df = post_df.reindex(columns=new_order)

    # Convert dtypes of columns

    convert_dict = {
        "p_likes": int,
        "p_comments": int,
        "c_id": object,
        "c_reply_to": object,
        "c_likes": int,
    }
    post_df = post_df.astype(convert_dict)

    return post_df


def save_dataframe(df, filename):

    try:
        base_df = pd.read_csv(filename)

    except (FileNotFoundError):
        base_df = pd.DataFrame()

    new_df = pd.concat([base_df, df])

    new_df.to_csv(filename, index=False)


def get_file_path(prefix):

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    comments_folder = os.path.abspath("../comments")
    filename = f"{prefix}_{timestamp}.csv"
    file_path = os.path.join(comments_folder, filename)

    return file_path


def main():

    settings = read_config()
    print(f"Loaded settings at {(strftime('%X %x'))}")

    driver = load_driver()
    print(f"Loaded driver at {(strftime('%X %x'))}")

    if settings["scraping_mode"] == "posts":

        export_path = get_file_path(prefix="posts")

        print("Reading post list")
        post_list = open("posts.txt", "r").read().splitlines()

        for post in post_list:

            print(
                f"Scraping post {post_list.index(post)+1} of {len(post_list)}")
            post_df = scrape_post(driver, post)

            save_dataframe(post_df, export_path)

        print(f"Database exported: {export_path}")

    driver.quit()


if __name__ == '__main__':
    main()
