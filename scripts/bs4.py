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

    soup = BeautifulSoup(response, "html.parser")

    # Initialize dataframe instance, and set post metadata to None
    post_df = pd.DataFrame()
    post_caption = post_ig_id = post_like_count = post_media_type = post_shortcode = post_timestamp = post_username = post_views_count = post_location = post_location_id = None

    # Search for a script that contains the post metadata
    json_info = json.loads(soup.select("script[type='application/ld+json']")[0].string)

    try:
        shortcode = json_info["mainEntityofPage"]["@id"]
        post_shortcode = match(r"https:\/\/www\.instagram\.com\/p\/(.+)\/", shortcode)[1]
    except IndexError:
        pass

    try:
        caption = soup.select("script[type='application/ld+json']")[0]
        p_caption = json.loads(caption.string)["caption"]
    except IndexError:
        pass

    try:
        if driver.find_elements_by_css_selector("._97aPb > .ZyFrc"):
            post_media_type = "IMAGE"
        elif driver.find_elements_by_css_selector("._97aPb > div > .kPFhm"):
            post_media_type = "VIDEO"
        elif driver.find_elements_by_css_selector("._97aPb > .rQDP3"):
            post_media_type = "CAROUSEL_ALBUM"
    except NoSuchElementException:
        pass

    try:
        post_timestamp = soup.select(".c-Yi7 > time").get_attribute("datetime")
        post_timestamp = datetime.strptime(post_timestamp, r"%Y-%m-%dT%H:%M:%S.%fZ")
        post_username = driver.find_elements_by_css_selector("a.ZIAjV")[0].text
    except NoSuchElementException:
        pass

    try:
        post_like_count = soup.select(".Nm9Fw span").text
        post_like_count = int(post_like_count.replace(",", ""))
    except NoSuchElementException:
        # On video posts, you have to click the "views count" span for the likes count to appear
        try:
            views = soup.select(".vcOH2")
            views.click()
            m = match(r"(\d+)", views.text.replace(",", ""))
            if m: post_views_count = int(m[0])
            else: post_views_count = 0

            post_like_count = soup.select(".vJRqr span").text
            post_like_count = int(post_like_count.replace(",", ""))            

            # click out of the views pop-up to prevent ElementClickInterceptedException
            soup.select(".QhbhU").click()
        except NoSuchElementException:
            pass
    
    try:
        location = soup.select(".O4GlU")
        post_location = location.text
        m = match(r"https:\/\/www\.instagram\.com\/explore\/locations\/(\d+)\/.*", location.get_attribute("href"))
        post_location_id = m[1]
    except NoSuchElementException:
        pass

    try:
        ig_id = soup.select("meta[property='al:ios:url']")
        m = match(r"instagram:\/\/media\?id=(\d+)", ig_id.get_attribute("content"))
        post_ig_id = m[1]
    except NoSuchElementException:
        pass

    # Fill dataframe with values, which will be None if not found
    post_df["p_caption"] = [post_caption]
    post_df["p_ig_id"] = [post_ig_id]
    post_df["p_like_count"] = [post_like_count]
    post_df["p_media_type"] = [post_media_type]
    # post_df["p_permalink"] = [post_permalink]
    post_df["p_shortcode"] = [post_shortcode]
    post_df["p_timestamp"] = [post_timestamp]
    post_df["p_username"] = [post_username]
    post_df["p_views_count"] = [post_views_count]
    post_df["p_location"] = [post_location]
    post_df["p_location_id"] = [post_location_id]

    if comments:
        try:
            load_comments()
            if replies:
                load_replies()

            comments_df = pd.DataFrame()

            for comment in driver.find_elements_by_css_selector("ul.XQXOT > ul.Mr508 > div.ZyFrc div.C4VMK"):
                driver.execute_script("arguments[0].scrollIntoView();", comment)
                comment_df = get_comment_info(comment)
                comments_df = pd.concat([comments_df, comment_df])

            post_df = pd.concat([post_df] * len(comments_df.index)) # Repeat the post_df rows to match the comments count
            post_df = pd.concat([post_df, comments_df], axis=1) # Join the two dataframes together, side to side horizontally
        except ValueError: # empty df
            pass

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


r = requests.get(post).text
with open("requests.html", "w+", encoding="utf-8") as f:
    f.write(r)