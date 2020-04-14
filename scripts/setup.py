import scraper
import igram

import pandas as pd

from datetime import datetime
from time import strftime


def load_settings():

    config_parser = ConfigParser()

    config_parser.read('credentials.txt')
    login_username = config_parser.get('credentials', 'user')
    login_password = config_parser.get('credentials', 'password')

    config_parser.read('scraper_config.txt')

    scraping_mode = config_parser.get('scraping', 'scraping_mode')

    get_accounts_dict = config_parser.getboolean('dicts', 'get_accounts_dict')
    get_posts_dict = config_parser.getboolean('dicts', 'get_posts_dict')
    number_of_posts = int(config_parser.get('dicts', 'number_of_posts'))

    since = config_parser.get('period', 'since').replace("-", "")
    until = config_parser.get('period', 'until').replace("-", "")

    settings = {
        'login_username': login_username,
        'login_password': login_password,
        'get_posts_dict': get_posts_dict,
        'get_accounts_dict': get_accounts_dict,
        'number_of_posts': number_of_posts,
        'scraping_mode': scraping_mode,
        "period_since": since,
        "period_until": until,
    }

    return settings


def get_posts_by_period(user_list):

    posts_dict = {}

    since = int(datetime.strptime(settings['since'], "%Y%m%d").timestamp())
    until = int(datetime.strptime(settings['until'], "%Y%m%d").timestamp())

    for user in user_list:

        posts_dict[user] = []

        path = f'../dictionaries/{user}/posts'

        master = pd.read_csv(f"{path}/master.csv")

        within_period = (master['created_at'] >= since) & (
            master['created_at'] <= until)

        posts_dict[user] = master[within_period]['short_code'].tolist()

        # for file in file_list:

        #     short_code = file.name[:-5]

        #     posts_dict[user].append(short_code)

    return posts_dict


def main():

    settings = load_settings()
    print(f"Loaded settings at {(strftime('%X %x'))}")

    if settings['scraping_mode'] == "by_posts":
        print("Retrieveing post list")
        posts_dict = {}
        posts_dict['default'] = []
        posts_dict['default'] = open("posts.txt", "r").read().splitlines()

        print("Scraping Instagram posts")
        scraper.main(posts_dict, mode="by_posts")

    elif settings['scraping_mode'] == "by_period":
        print("Getting user list")
        user_list = open("users.txt", "r").read().splitlines()

        if settings['get_accounts_dict']:
            print(f"Getting account dictionaries at {strftime('%X %x')}")
            igram.get_account_dict(settings, user_list)

        if settings['get_posts_dict']:
            print(f"Getting posts dictionaries at {strftime('%X %x')}")
            igram.get_media_dict(settings, user_list)

        print(
            f"Retrieving posts by period: {settings['since']} - {settings['until']}")
        posts_dict = get_posts_by_period(user_list)

        scraper.main(posts_dict, mode="by_period")
