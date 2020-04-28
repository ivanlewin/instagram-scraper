import json
import os
import pandas as pd
from datetime import datetime
from igramscraper import instagram
from pandas.errors import EmptyDataError


def read_credentials():

    with open("credentials.txt", "r") as file:
        return file.read().split(",")


def login_ig(user, pwd):

    global ig

    ig = instagram.Instagram()
    ig.with_credentials(user, pwd, os.getcwd())
    ig.login()


def get_account_dicts(userlist, timestamp):
    '''Crea un json con toda la info de cada user obtenida a través de la API de Instagram'''

    folder = os.path.abspath("../dictionaries/accounts")

    for user in userlist:

        account = ig.get_account(user)
        account_info = account.__dict__

        file_path = os.path.join(folder, f"{user}.json")
        with open(file_path, 'w+') as file:
            json.dump(account_info, file)


def get_media_dicts(userlist, n):
    '''Hace un request a la API de Instagram de los últimos n posts de cada usuario
    y exporta la información de cada uno en un json'''

    for user in userlist:

        export_folder = os.path.abspath(f"../dictionaries/posts/{user}")
        if not os.path.exists(export_folder):
            os.mkdir(export_folder)

        posts = ig.get_medias(user, n)

        for post in posts:

            post = post.__dict__

            post.pop("owner", None)

            with open(f'{export_folder}/{post["short_code"]}.json', 'w') as file:
                json.dump(post, file)

            add_to_master(post, user)


def add_to_master(post, user):

    post_df = pd.DataFrame(
        {
            "p_id": post['short_code'],
            "p_author": user,
            "p_date": post['created_time'],
            "p_link": post['link'],
        }, index=[0]
    )

    try:

        master_path = os.path.abspath("../dictionaries/posts/master.csv")
        master = pd.read_csv(master_path)

        if post['short_code'] not in master['p_id'].values:
            master = pd.concat([master, post_df])
            master.to_csv(master_path, index=False)

    except (FileNotFoundError, EmptyDataError):
        post_df.to_csv(master_path, index=False)


def main(timestamp=datetime.now().strftime("%Y%m%d-%H%M%S"), **kwargs):

    with open("users.txt", "r") as file:
        userlist = file.read().splitlines()

    user, pwd = read_credentials()

    print("Logging in with credentials")
    login_ig(user, pwd)

    if kwargs["create_accounts_dict"]:

        print("Creating account dictionaries")
        get_account_dicts(userlist, timestamp)

    if kwargs["create_posts_dict"]:

        print("Creating post dictionaries")
        get_media_dicts(userlist, kwargs["number_of_posts"])


if __name__ == '__main__':

    default_config = {
        'create_accounts_dict': True,
        'create_posts_dict': True,
        'number_of_posts': 3
    }

    main(**default_config)
