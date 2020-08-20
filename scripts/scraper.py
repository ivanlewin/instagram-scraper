import json
import os
import pandas as pd
from bs4 import BeautifulSoup
from configparser import ConfigParser
from datetime import datetime
from pandas.errors import EmptyDataError
from re import match
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException
from time import sleep


def main(**kwargs):

    # config del txt
    comments = kwargs.get("comments")
    replies = kwargs.get("replies")
    output_folder = kwargs.get("custom_folder")

    post_dict = read_posts()
    driver = load_driver()

    for user in post_dict:

        save_path = get_file_path(user, output_folder)

        for post in post_dict[user]:
            print(f"Usuario: {user} | Posteo {post_dict[user].index(post)+1}/{len(post_dict[user])}")

            driver.get(post)
            sleep(2)
            post_df = scrape_post(driver.page_source)

            if comments:
                print("Scrapeando comentarios")

                comments_df = scrape_comments(driver, replies=replies)

                try:
                    post_df = pd.concat([post_df] * len(comments_df.index))  # Multiplicar la row del posteo por la cantidad de comments
                    post_df = pd.concat([post_df, comments_df], axis=1)  # Unir los dataframes lado a lado horizontalmente

                except ValueError:  # Dataframe vacío
                    pass

            save_dataframe(post_df, save_path)
        print(f"Archivo guardado: {save_path}\n")

    driver.quit()


def read_config():

    config = ConfigParser()
    config.read('./scripts/config.txt')

    comments = config.getboolean("comments", "scrape_comments")
    replies = config.getboolean("comments", "scrape_replies")
    custom_folder = config.get("output", "output_folder")

    settings = {
        "comments": comments,
        "replies": replies,
        "custom_folder": custom_folder if custom_folder != "" else None,
    }

    return settings


def read_posts():
    posts = {}
    folder = "./posts"
    files = [file for file in os.listdir(folder) if file != ".gitkeep"]  # Ignorar archivo .gitkeep
    for file in files:
        user, _ = os.path.splitext(file)
        if user:
            with open(os.path.join(folder, file), "r") as f:
                posts[user] = [p for p in f.read().splitlines()]

    return posts


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
                profile = os.path.join(profiles_folder, os.listdir(profiles_folder)[0])  # Usa el primer perfil de la carpeta

            firefox_profile = webdriver.FirefoxProfile(profile_directory=profile)
            driver = webdriver.Firefox(firefox_profile)

        else:
            driver = webdriver.Firefox()

    if driver == "Chrome":

        if existing_profile:

            if not profile:
                profile = os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data")  # Usa el perfil por defecto

            options = webdriver.ChromeOptions()
            options.add_argument("user-data-dir=" + profile)
            driver = webdriver.Chrome(chrome_options=options)

        else:
            driver = webdriver.Chrome()

    return driver


def scrape_post(post_html):

    # Inicializo las columnas en None
    post_comments_count = post_caption = post_ig_id = post_like_count = post_media_type = post_shortcode = post_timestamp = post_username = post_views_count = post_location = post_location_id = None

    soup = BeautifulSoup(post_html, "html.parser")

    # Selecciono el script que tiene la metadata del posteo
    for script in soup.select("script[type='text/javascript']"):
        if (script.string and script.string.startswith("window._sharedData")):
            json_string = script.string.replace("window._sharedData = ", "")[:-1]
            post_info = json.loads(json_string)

    try:
        post_json = post_info["entry_data"]["PostPage"][0]["graphql"]["shortcode_media"]
    except KeyError:  # Puede que sea un posteo privado
        post_json = post_info["entry_data"]["ProfilePage"][0]["graphql"]["user"]

    comments_count = post_json.get("edge_media_to_parent_comment").get("count")
    if comments_count:
        post_comments_count = int(comments_count)

    try:
        post_caption = post_json["edge_media_to_caption"]["edges"][0]["node"]["text"]
    except IndexError:  # Sin descripción
        pass

    post_ig_id = post_json.get("id")

    comments_enabled = post_json.get("comments_disabled")
    if comments_enabled is not None:
        post_is_comment_enabled = not(comments_enabled)

    like_count = post_json.get("edge_media_preview_like").get("count")
    if like_count:
        post_like_count = int(like_count)
    post_shortcode = post_json.get("shortcode")

    owner = post_json.get("owner")
    if owner:
        post_username = owner.get("username")
        post_owner = owner.get("id")

    location = post_json.get("location")
    if location:
        post_location = location.get("name")
        post_location_id = location.get("id")

    media_type = post_json.get("__typename")
    if media_type == "GraphImage":
        post_media_type = "IMAGE"
    elif media_type == "GraphSidecar":
        post_media_type = "CAROUSEL_ALBUM"
    elif media_type == "GraphVideo":
        post_media_type = "VIDEO"

    post_views_count = post_json.get("video_view_count")

    timestamp = soup.select_one(".c-Yi7 > time")["datetime"]
    post_timestamp = datetime.strptime(timestamp, r"%Y-%m-%dT%H:%M:%S.%fZ")

    # armo el dataframe con la información scrapeada
    post_df = pd.DataFrame({
        "p_comments_count": [post_comments_count],
        "p_caption": [post_caption],
        "p_id": [post_id],
        "p_ig_id": [post_ig_id],
        "p_is_comment_enabled": [post_is_comment_enabled],
        "p_like_count": [post_like_count],
        "p_media_type": [post_media_type],
        # "p_media_url": = [post_media_url],
        "p_owner": [post_owner],
        # "p_permalink": [post_permalink],
        "p_shortcode": [post_shortcode],
        "p_timestamp": [post_timestamp],
        "p_username": [post_username],
        "p_views_count": [post_views_count],
        "p_location": [post_location],
        "p_location_id": [post_location_id],
    })

    # cambio el datatype de las columnas de id a strings para que no los castee a numbers
    post_df = post_df.astype({"p_ig_id": object, "p_owner": object, "p_location_id": object})

    return post_df


def scrape_comments(driver, replies=False):

    def load_comments():
        """Clickea el boton de "Load more comments" hasta que no encuentre nuevos comments."""
        while True:
            try:
                load_more_comments = driver.find_element_by_css_selector("button.dCJp8")
                load_more_comments.click()
                sleep(2)
            except NoSuchElementException:
                break

    def load_replies():
        """Clickea todos los botones de 'x reply(ies)' hasta que no encuentre ninguno."""
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

        # Inicializo las columnas en None
        comment_id = comment_reply_id = comment_timestamp = comment_username = comment_text = comment_like_count = None

        try:
            comment_username = comment.find_element_by_css_selector("h3 a").text
            comment_text = comment.find_element_by_css_selector("span:not([class*='coreSpriteVerifiedBadgeSmall'])").text

            info = comment.find_element_by_css_selector(".aGBdT > div")

            permalink = info.find_element_by_css_selector("a")
            m = match(r"(?:https:\/\/www\.instagram\.com\/p\/.+)\/c\/(\d+)(?:\/)(?:r\/(\d+)\/)?", permalink.get_attribute("href"))
            comment_id = m[1]
            comment_reply_id = m[2]

            comment_timestamp = info.find_element_by_tag_name("time").get_attribute("datetime")
            comment_timestamp = datetime.strptime(comment_timestamp, r"%Y-%m-%dT%H:%M:%S.%fZ")

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
            "c_reply_id": [comment_reply_id],
        })

        # cambio el datatype de las columnas de id a strings para que no los castee a numbers
        comment_df = comment_df.astype({"c_id": object, "c_reply_id": object})

        return comment_df

    comments_df = pd.DataFrame()

    load_comments()
    if replies:
        load_replies()

    try:
        for comment in driver.find_elements_by_css_selector("ul.XQXOT > ul.Mr508 div.ZyFrc div.C4VMK"):
            driver.execute_script("arguments[0].scrollIntoView();", comment)  # scrollear hasta tener el comment en foco
            comment_df = get_comment_info(comment)
            comments_df = pd.concat([comments_df, comment_df])

    except ValueError:  # df vacío
        pass

    return comments_df


def save_dataframe(df, path):

    try:
        base_df = pd.read_csv(path)
        new_df = pd.concat([base_df, df])
        new_df.to_csv(path, index=False)

    except (FileNotFoundError, EmptyDataError):
        df.to_csv(path, index=False)


def get_file_path(prefix, output_folder, timestamp=datetime.now().strftime(r"%Y%m%d")):

    # usar la output_folder si la hay, o la carpeta "/csv" por defecto
    if output_folder is not None:
        folder = os.path.abspath(output_folder)
    else:
        folder = os.path.abspath("./csv")

    if not os.path.exists(folder):
        os.mkdir(folder)

    filename = f"{prefix}_{timestamp}.csv"

    return os.path.join(folder, filename)


if __name__ == "__main__":
    config = read_config()
    main(**config)
