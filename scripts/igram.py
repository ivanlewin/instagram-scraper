import pandas as pd
import json
import os
from igramscraper import instagram
from pandas.errors import EmptyDataError


def login_ig(username, password):

    login_username = settings['login_username']
    login_password = settings['login_password']

    ig = instagram.Instagram()
    ig.with_credentials(login_username, login_password, os.getcwd())
    ig.login()

    return ig


def get_account_dict(settings, userlist):

    ig = login_ig(settings)

    account_info = dict()

    for user in (userlist):

        # request a Instagram de la info de la cuenta (usa API)
        account = ig.get_account(user)

        # Crea el diccionario con toda la info de cada user
        account_info[user] = account.__dict__

        path = f'../dictionaries/{user}'

        if not os.path.exists(path):
            os.makedirs(path)

        # Exporta el diccionario con la info de la cuentas
        with open(f'{path}/account.json', 'w+') as file:
            json.dump(account_info, file)




def get_media_dict(settings, userlist):

    ig = login_ig(settings)

    cant_of_posts = settings['n_of_posts']

    for user in userlist:

        path = f'../dictionaries/{user}/posts'

        if not os.path.exists(path):
            os.makedirs(path)

        # request a Instagram la info de los últimos n posteos del user (usa API)
        posts = ig.get_medias(user, cant_of_posts)

        try:
            master = pd.read_csv(f'{path}/master.csv')

        except (FileNotFoundError, EmptyDataError):
            master = pd.DataFrame(
                columns=["short_code", "link", "user", "created_at"])

        for post in posts:

            post = post.__dict__

            short_code = post['short_code']
            link = post['link']
            created_at = post['created_time']

            with open(f'{path}/{short_code}.json', 'w+') as file:
                json.dump(post, file)

            post_df = pd.DataFrame({
                "short_code": short_code,
                "link": link,
                "user": user,
                "created_at": created_at}, index=[0])

            if short_code not in master['short_code'].values:
                master = pd.concat([master, post_df])
                master.to_csv(f"{path}/master.csv", index=False)

        # Hay que cambiar line 181 de media.py:
        # self.owner = Account(arr[prop]) -> self.owner = None