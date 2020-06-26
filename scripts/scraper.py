import os
import pandas as pd
from pandas.errors import EmptyDataError
from datetime import datetime
from re import match
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from time import sleep


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
                profile = os.path.join(profiles_folder, os.listdir(profiles_folder)[0]) # Selecting first profile in the folder

            firefox_profile = webdriver.FirefoxProfile(profile_directory=profile)
            driver = webdriver.Firefox(firefox_profile)
        
        else: driver = webdriver.Firefox()

    if driver == "Chrome":

        if existing_profile:

            if not profile:
                profile = os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\User Data") # Selects Default profile

            options = webdriver.ChromeOptions()
            options.add_argument('user-data-dir=' + profile)
            driver = webdriver.Chrome(chrome_options=options)            

        else: driver = webdriver.Chrome()
    
    return driver

def scrape_post(driver, comments=True, replies=True):
    
    def load_comments():
        """Clicks the 'Load more comments' button until there are no more comments."""
        while True:
            try:            
                load_more_comments = driver.find_element_by_css_selector('button.dCJp8')
                load_more_comments.click()
                sleep(2)
            except NoSuchElementException:
                break

    def load_replies():
        try:
            view_replies_buttons = driver.find_elements_by_css_selector('.y3zKF')

            for button in view_replies_buttons:

                driver.execute_script("arguments[0].scrollIntoView();", button)

                try:
                    text = driver.execute_script(
                        "return arguments[0].textContent;", button)
                    while "Ver" in text or "View" in text:
                        button.click()
                        sleep(0.5)
                        text = driver.execute_script(
                            "return arguments[0].textContent;", button)
                            
                except StaleElementReferenceException:
                    pass

        except NoSuchElementException:
            pass

    def get_comment_info(comment):

        comment_id = comment_reply_id = comment_created_at = comment_author = comment_content = comment_likes_count = None

        try:
            comment_author = comment.find_element_by_css_selector('h3 a').text
            comment_content = comment.find_element_by_css_selector('span:not([class*="coreSpriteVerifiedBadgeSmall"])').text

            info = comment.find_element_by_css_selector('.aGBdT > div')
            
            permalink = info.find_element_by_css_selector('a')
            m = match(r"(?:https:\/\/www\.instagram\.com\/p\/.+)\/c\/(\d+)(?:\/)(?:r\/(\d+)\/)?", permalink.get_attribute('href'))
            comment_id = m[1]
            comment_reply_id = m[2]

            comment_created_at = info.find_element_by_tag_name('time').get_attribute('datetime')
            comment_created_at = datetime.strptime(comment_created_at, r"%Y-%m-%dT%H:%M:%S.%fZ")
            # comment_created_at = datetime.timestamp(comment_created_at)

            likes = info.find_element_by_css_selector('button.FH9sR').text
            m = match(r"(\d+)", likes)
            if m:
                comment_likes_count = int(m[0])
            else:
                comment_likes_count = 0

        except NoSuchElementException:
            pass

        comment_df = pd.DataFrame({
            "c_id": [comment_id],
            "c_reply_id": [comment_reply_id],
            "c_author": [comment_author],
            "c_content": [comment_content],
            "c_likes_count": [comment_likes_count],
            "c_created_at": [comment_created_at],
        })

        # convert_dict = {
        #     "c_id": object,
        #     "c_reply_id": object,
        # }

        # comment_df = comment_df.astype(convert_dict)

        return comment_df

    post_df = pd.DataFrame()

    post_id = post_created_at = post_author = post_likes_count = post_comments_count = None

    post_id = match(r"https:\/\/www\.instagram\.com\/p\/(.+)\/", driver.current_url)[1]

    try:
        post_created_at = driver.find_element_by_css_selector(".c-Yi7 > time").get_attribute('datetime')
        post_created_at = datetime.strptime(post_created_at, r"%Y-%m-%dT%H:%M:%S.%fZ")
        # post_created_at = datetime.timestamp(post_created_at)

        post_author = driver.find_elements_by_css_selector("a.ZIAjV")[0].text
    except NoSuchElementException:
        pass

    try:
        post_likes_count = driver.find_element_by_css_selector(".Nm9Fw span").text
        post_likes_count = int(post_likes_count.replace(",", ""))
    except NoSuchElementException:
        # On video posts, you have to click the 'views count' span for the likes count to appear
        try:
            driver.find_element_by_css_selector(".vcOH2").click()
            post_likes_count = driver.find_element_by_css_selector(".vJRqr span").text
            post_likes_count = int(post_likes_count.replace(",", ""))
        except NoSuchElementException:
            pass
    
    try:
        post_df["p_id"] = [post_id]
        post_df["p_author"] = [post_author]
        post_df["p_likes_count"] = [post_likes_count]
        post_df["p_created_at"] = [post_created_at]
            
    except KeyError: # empty post_df
            pass

    if comments:
        load_comments()
        if replies:
            load_replies()

        comments_df = pd.DataFrame()

        for comment in driver.find_elements_by_css_selector('ul.Mr508 div.ZyFrc div.C4VMK'):
            driver.execute_script("arguments[0].scrollIntoView();", comment)
            comment_df = get_comment_info(comment)
            comments_df = pd.concat([comments_df, comment_df])

        post_df = pd.concat([post_df] * len(comments_df.index)) # Repeat the post_df rows to match the comments count
        post_df = pd.concat([post_df, comments_df], axis=1) # Join the two dataframes together, side to side horizontally

    return post_df


def save_dataframe(df, path):

    try:
        base_df = pd.read_csv(path)
        new_df = pd.concat([base_df, df])
        new_df.to_csv(path, index=False)

    except (FileNotFoundError, EmptyDataError):
        df.to_csv(path, index=False)


def get_file_path(timestamp, prefix):

    comments_folder = os.path.abspath("../comments")
    if not os.path.exists(comments_folder):
        os.mkdir(comments_folder)
    filename = f"{prefix}_{timestamp}.csv"
    file_path = os.path.join(comments_folder, filename)

    return file_path


def posts_from_master(userlist, period):

    master_path = os.path.abspath("../dictionaries/posts/master.csv")
    master_df = pd.read_csv(master_path)

    since_ts, until_ts = period

    filtered_df = master_df.loc[master_df['p_author'].isin(userlist)]
    filtered_df = filtered_df[filtered_df['p_date'].between(
        since_ts, until_ts)]

    filtered_df = filtered_df.drop(columns=["p_id", "p_date"])

    posts = list(filtered_df.to_records(index=False))

    return posts


def main(timestamp=datetime.now().strftime("%Y%m%d-%H%M%S"), **kwargs):

    driver = load_driver()

    if kwargs['scraping_mode'] == "post_list":

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

    if kwargs['scraping_mode'] == "master_file":

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


if __name__ == '__main__':

    default_config = {'scraping_mode': 'master_file',
    'period': (0, datetime.timestamp(datetime.now()))}

    # main(**default_config)
