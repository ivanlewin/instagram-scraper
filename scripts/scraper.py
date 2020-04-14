import pandas as pd
import os

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from time import sleep, strftime
from re import match


def load_driver():

    # Find Firefox Profile
    profiles_folder = f"{os.environ['appdata']}\Mozilla\Firefox\Profiles"
    for folder in os.listdir(profiles_folder):
        if "default-release" in folder:
            firefox_profile = webdriver.FirefoxProfile(
                f"{profiles_folder}/{folder}")
            driver = webdriver.Firefox(firefox_profile)
            break

        else:
            driver = webdriver.Firefox()

    driver.get('https://www.instagram.com/p/B8o367kgObt/')

    try:
        close_button = driver.find_element_by_css_selector('.xqRnw')
        close_button.click()

    except NoSuchElementException:
        pass

    return driver


def post_scraper(post):

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

        comment_df = get_comment_info(comment)
        post_df = pd.concat([post_df, comment_df])

    return post_df


def get_comment_info(comment):

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


def main(posts_dict, mode="by_post"):

    load_driver()

    now = datetime.now()
    print(type(now))
    print(now.strftime("%H%M%S"))

    base_df = pd.DataFrame()

    if mode == "by_period":

        for user in posts_dict:
            print(f"Scraping {user}'s posts")

            path = f'../comments/{user}'
            if not os.path.exists(path):
                os.makedirs(path)

            for code in posts_dict[user]:
                print(
                    f"Post {posts_dict[user].index(code)+1} of {len(posts_dict[user])}")

                link = f"https://www.instagram.com/p/{code}"

                post_df = post_scraper(link)
                base_df = pd.concat([base_df, post_df])

                base_df.to_csv(
                    f"../comments/{user}_{now.strftime('%Y%m%d')}.csv", index=False)

    if mode == "by_post":

        for link in posts_dict['default']:

            print(
                f"Post {posts_dict['default'].index(link)+1} of {len(posts_dict['default'])}")

            code = match(r"https:\/\/www\.instagram\.com\/p\/(.*)/?", link)[1]

            post_df = post_scraper(link)
            base_df = pd.concat([base_df, post_df])

            base_df.to_csv(
                f"../comments/{now.strftime('%Y%m%d_%H%M%S')}.csv", index=False)

    print("Exported comments")
    driver.quit()
