import json
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from configparser import ConfigParser
from datetime import datetime
from pandas.errors import EmptyDataError
from re import match, search
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from time import sleep


def read_config():

    config = ConfigParser()

    config.read('./scripts/config.txt')

    comments = config.getboolean("comments", "comments")
    replies = config.getboolean("comments", "replies")

    settings = {
        "comments": comments,
        "replies": replies,
    }

    return settings


def read_posts():
    posts = {}
    folder = "./posts"
    for file in os.listdir(folder)[1:]:  # Ignore the .gitkeep file
        user, _ = os.path.splitext(file)
        if user:
            with open(os.path.join(folder, file), "r") as f:
                posts[user] = [p for p in f.read().splitlines()]

    return posts


def bs4_parse(post_html):

    # Initialize dataframe instance, and set post metadata to None
    post_df = pd.DataFrame()
    post_comments_count = post_caption = post_ig_id = post_is_comment_enabled = post_like_count = post_media_type = post_owner = post_shortcode = post_timestamp = post_username = post_views_count = post_location = post_location_id = None

    soup = BeautifulSoup(post_html, "html.parser")

    # Search for a script that contains the post metadata
    for script in soup.select("script[type='text/javascript']"):
        if (script.string and script.string.startswith("window._sharedData")):
            json_string = script.string.replace("window._sharedData = ", "")
            json_string = json_string[:-1]
            json_object = json.loads(json_string)
            post_json = json_object["entry_data"]["PostPage"][0]["graphql"]["shortcode_media"]

    post_comments_count = int(post_json["edge_media_to_parent_comment"]["count"])

    try:
        post_caption = post_json["edge_media_to_caption"]["edges"][0]["node"]["text"]
    except IndexError:  # No caption
        pass

    post_ig_id = post_json["id"]
    post_is_comment_enabled = not (post_json["comments_disabled"])
    post_like_count = int(post_json["edge_media_preview_like"]["count"])
    post_shortcode = post_json["shortcode"]
    post_username = post_json["owner"]["username"]
    post_owner = post_json["owner"]["id"]

    try:
        post_location = post_json["location"]["name"]
        post_location_id = post_json["location"]["id"]
    except TypeError:  # Catch TypeError when post_json["location"] is None
        pass

    media_type = post_json["__typename"]
    if media_type == "GraphImage":
        post_media_type = "IMAGE"
    elif media_type == "GraphSidecar":
        post_media_type = "CAROUSEL_ALBUM"
    else:
        post_media_type = "VIDEO"

    try:
        post_views_count = post_json["video_view_count"]
    except KeyError:  # Catch KeyError for non-video posts
        pass

    # On some posts there is a script that contains the full timestamp info, ISO8601 formatted
    try:
        timestamp_string = soup.select("script[type='application/ld+json']")[0].string
        timestamp_json = json.loads(timestamp_string)
        timestamp = timestamp_json["uploadDate"]
        post_timestamp = datetime.strptime(timestamp, r"%Y-%m-%dT%H:%M:%S")
    except IndexError:
        try:
            if post_media_type == "IMAGE":
                date = post_json["accessibility_caption"]
            elif post_media_type == "CAROUSEL_ALBUM":
                date = post_json["edge_sidecar_to_children"]["edges"][0]["node"]["accessibility_caption"]
            else:
                date = post_json["accessibility_caption"]
            m = match(r"^.* on (.*, \d{4})", date)
            post_timestamp = datetime.strptime(m[1], "%B %d, %Y")
        except:
            pass

    # Fill dataframe with values, which will be None if not found
    post_df["p_comments_count"] = [post_comments_count]
    post_df["p_caption"] = [post_caption]
    # post_df["p_id"] = [post_id]
    post_df["p_ig_id"] = [post_ig_id]
    post_df["p_is_comment_enabled"] = [post_is_comment_enabled]
    post_df["p_like_count"] = [post_like_count]
    post_df["p_media_type"] = [post_media_type]
    # post_df["p_media_url"] = [post_media_url]
    post_df["p_owner"] = [post_owner]
    # post_df["p_permalink"] = [post_permalink]
    post_df["p_shortcode"] = [post_shortcode]
    post_df["p_timestamp"] = [post_timestamp]
    post_df["p_username"] = [post_username]
    post_df["p_views_count"] = [post_views_count]
    post_df["p_location"] = [post_location]
    post_df["p_location_id"] = [post_location_id]

    return post_df


def load_driver(driver="Firefox", existing_profile=False, profile=None):
    """Loads and returns a webdriver instance.

    Keyword arguments:
    driver -- which driver you want to use
        "Chrome" for chromedriver or "Firefox" for geckodriver.
    existing_profile -- wether you want to use an existing browser profile,
        which grants access to cookies and other session data.
    profile -- the path to the profile you want to use.
        By default it will look into the default profiles_folder for the selected browser
        and choose the first one, but it may be the case that you want to use another one.
    """
    if driver == "Firefox":

        if existing_profile:

            if not profile:
                profiles_folder = os.path.expandvars("%APPDATA%\\Mozilla\\Firefox\\Profiles")
                profile = os.path.join(profiles_folder, os.listdir(profiles_folder)[0])  # Selecting first profile in the folder

            firefox_profile = webdriver.FirefoxProfile(profile_directory=profile)
            driver = webdriver.Firefox(firefox_profile)

        else:
            driver = webdriver.Firefox()

    if driver == "Chrome":

        if existing_profile:

            if not profile:
                profile = os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data")  # Selects Default profile

            options = webdriver.ChromeOptions()
            options.add_argument("user-data-dir=" + profile)
            driver = webdriver.Chrome(chrome_options=options)

        else:
            driver = webdriver.Chrome()

    return driver


def scrape_comments(driver, replies=False):

    def load_comments():
        """Clicks the "Load more comments" button until there are no more comments."""
        while True:
            try:
                load_more_comments = driver.find_element_by_css_selector("button.dCJp8")
                load_more_comments.click()
                sleep(2)
            except NoSuchElementException:
                break

    def load_replies():
        try:
            view_replies_buttons = driver.find_elements_by_css_selector(".y3zKF")

            for button in view_replies_buttons:

                try:
                    driver.execute_script("arguments[0].scrollIntoView();", button)

                    text = button.text
                    while "Ver" in text or "View" in text:
                        button.click()
                        sleep(0.5)
                        text = button.text

                except (StaleElementReferenceException, ElementClickInterceptedException):
                    pass

        except (NoSuchElementException):
            pass

    def get_comment_info(comment):

        comment_id = comment_parent_id = comment_timestamp = comment_username = comment_text = comment_like_count = None

        try:
            comment_username = comment.find_element_by_css_selector("h3 a").text
            comment_text = comment.find_element_by_css_selector("span:not([class*='coreSpriteVerifiedBadgeSmall'])").text

            info = comment.find_element_by_css_selector(".aGBdT > div")

            permalink = info.find_element_by_css_selector("a")
            m = match(r"(?:https:\/\/www\.instagram\.com\/p\/.+)\/c\/(\d+)(?:\/)(?:r\/(\d+)\/)?", permalink.get_attribute("href"))
            if m[2]:
                comment_id = m[2]
                comment_parent_id = m[1]
            else:
                comment_id = m[1]

            comment_timestamp = info.find_element_by_tag_name("time").get_attribute("datetime")
            comment_timestamp = datetime.strptime(comment_timestamp, r"%Y-%m-%dT%H:%M:%S.%fZ")
            # comment_timestamp = datetime.timestamp(comment_timestamp)

            likes = info.find_element_by_css_selector("button.FH9sR").text
            m = match(r"(\d+)", likes)
            if m:
                comment_like_count = int(m[0])
            else:
                comment_like_count = 0

        except NoSuchElementException:
            pass

        comment_df = pd.DataFrame({
            "c_username": [comment_username],
            "c_timestamp": [comment_timestamp],
            "c_text": [comment_text],
            "c_like_count": [comment_like_count],
            "c_id": [comment_id],
            "c_parent_id": [comment_parent_id],
        })

        comment_df = comment_df.astype({"c_id": object, "c_parent_id": object, })

        return comment_df

    comments_df = pd.DataFrame()

    load_comments()
    if replies:
        load_replies()

    try:
        for comment in driver.find_elements_by_css_selector("ul.XQXOT > ul.Mr508 div.ZyFrc div.C4VMK"):
            driver.execute_script("arguments[0].scrollIntoView();", comment)
            comment_df = get_comment_info(comment)
            comments_df = pd.concat([comments_df, comment_df])

    except ValueError:  # empty df
        pass

    return comments_df


def save_dataframe(df, path):

    try:
        base_df = pd.read_csv(path)
        new_df = pd.concat([base_df, df])
        new_df.to_csv(path, index=False)

    except (FileNotFoundError, EmptyDataError):
        df.to_csv(path, index=False)


def get_file_path(timestamp, prefix):

    comments_folder = os.path.abspath("./comments")
    if not os.path.exists(comments_folder):
        os.mkdir(comments_folder)
    filename = f"{prefix}_{timestamp}.csv"
    file_path = os.path.join(comments_folder, filename)

    return file_path


def posts_from_master(userlist, period):

    master_path = os.path.abspath("../dictionaries/posts/master.csv")
    master_df = pd.read_csv(master_path)

    since_ts, until_ts = period

    filtered_df = master_df.loc[master_df["p_username"].isin(userlist)]
    filtered_df = filtered_df[filtered_df["p_date"].between(since_ts, until_ts)]

    filtered_df = filtered_df.drop(columns=["p_shortcode", "p_date"])

    posts = list(filtered_df.to_records(index=False))

    return posts

def main(**kwargs):

    timestamp = datetime.now().strftime(r"%Y%m%d")
    post_dict = read_posts()
    comments = kwargs["comments"]
    replies = kwargs["replies"]
    driver = None

    for user in post_dict:

        dest_path = get_file_path(timestamp, user)

        for post in post_dict[user]:
            print(f"User: {user} | Post {post_dict[user].index(post)+1}/{len(post_dict[user])}")

            r = requests.get(post)
            post_df = bs4_parse(r.text)

            if comments:
                print("Scraping comments")

                if not driver:
                    driver = load_driver()

                driver.get(post)
                sleep(2)
                comments_df = scrape_comments(driver, replies=replies)

                try:
                    post_df = pd.concat([post_df] * len(comments_df.index))  # Repeat the post_df rows to match the comments count
                    post_df = pd.concat([post_df, comments_df], axis=1)  # Join the two dataframes together, side to side horizontally

                except ValueError:  # Empty df
                    pass

            save_dataframe(post_df, dest_path)
            print(f"Database saved: {dest_path}\n")


if __name__ == "__main__":
    config = read_config()
    main(config)
