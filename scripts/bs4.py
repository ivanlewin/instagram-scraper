import json
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pandas.errors import EmptyDataError
from datetime import datetime
from re import match
from time import sleep


def request_post(response):

    # Initialize dataframe instance, and set post metadata to None
    post_df = pd.DataFrame()
    post_comments_count = post_caption = post_ig_id = post_like_count = post_media_type = post_shortcode = post_timestamp = post_username = post_views_count = post_location = post_location_id = None
    
    soup = BeautifulSoup(response.text, "html.parser")

    # Search for a script that contains the post metadata
    for script in soup.select("script[type='text/javascript']"):
        if (script.string and script.string.startswith("window._sharedData")):
            json_string = script.string.replace("window._sharedData = ", "")
            json_string = json_string[:-1]
            json_object = json.loads(json_string)
            post_json = json_object["entry_data"]["PostPage"][0]["graphql"]["shortcode_media"]

    post_comments_count = int(post_json["edge_media_to_parent_comment"]["count"])
    post_caption = post_json["edge_media_to_caption"]["edges"][0]["node"]["text"]
    post_ig_id = post_json["id"]
    post_like_count = int(post_json["edge_media_preview_like"]["count"])
    post_shortcode = post_json["shortcode"]
    post_username = post_json["owner"]["username"]

    try:
        post_location = post_json["location"]["name"]
        post_location_id = post_json["location"]["id"]
    except TypeError: # Catch TypeError when post_json["location"] is None
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
    except KeyError: # Catch KeyError for non-video posts
        pass

    # The timestamp info is not on the script that contains the majority of the metadata
    timestamp_string = soup.select("script[type='application/ld+json']")[0].string
    timestamp_json = json.loads(timestamp_string)
    timestamp = timestamp_json["uploadDate"]
    post_timestamp = datetime.strptime(timestamp, r"%Y-%m-%dT%H:%M:%S")


    # Fill dataframe with values, which will be None if not found
    post_df["p_comments_count"] = [post_comments_count]
    post_df["p_caption"] = [post_caption]
    # post_df["p_id"] = [post_id]
    post_df["p_ig_id"] = [post_ig_id]
    # post_df["p_is_comment_enabled"] = [post_is_comment_enabled]
    post_df["p_like_count"] = [post_like_count]
    post_df["p_media_type"] = [post_media_type]
    # post_df["p_media_url"] = [post_media_url]
    # post_df["p_owner"] = [post_owner]
    # post_df["p_permalink"] = [post_permalink]
    post_df["p_shortcode"] = [post_shortcode]
    post_df["p_timestamp"] = [post_timestamp]
    post_df["p_username"] = [post_username]
    post_df["p_views_count"] = [post_views_count]
    post_df["p_location"] = [post_location]
    post_df["p_location_id"] = [post_location_id]

    return post_df


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


def main(timestamp=datetime.now().strftime(r"%Y%m%d-%H%M%S"), **kwargs):

    if kwargs["scraping_mode"] == "post_list":

        print("Retrieveing post list")

        with open("posts.txt", "r") as f:
            post_list = f.read().splitlines()

        file_path = get_file_path(timestamp, prefix="posts")

        for post in post_list:

            driver.get(post)
            sleep(2)
            df = scrape_post(driver)

            save_dataframe(df, file_path)

        print(f"Comments exported: {file_path}")

    if kwargs["scraping_mode"] == "master_file":

        print("Getting user list")
        with open("users.txt", "r") as file:
            userlist = file.read().splitlines()

        print("Reading master file")
        posts = posts_from_master(userlist, kwargs["period"])

        print("Scraping posts")

        for post in posts:

            user, link = post

            file_path = get_file_path(timestamp, prefix=user)
            df = scrape_post(driver, link)
            save_dataframe(df, file_path)

        print(f"Comments exported")

    driver.quit()


if __name__ == "__main__":

    default_config = {"scraping_mode": "master_file",
    "period": (0, datetime.timestamp(datetime.now()))}

    # main(**default_config)

response = requests.get(post)
r = response.text
soup = BeautifulSoup(r, "html.parser")
with open("requests.html", "w+", encoding="utf-8") as f:
    f.write(r)
driver.get(post)
with open("a.txt", "w+", encoding="utf-8") as f:
    f.write(json.dumps(post_json))