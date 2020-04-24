import igram_dicts
import scraper
from configparser import ConfigParser
from datetime import datetime
from time import strftime


def read_config():

    config = ConfigParser()

    config.read('config.txt')

    settings = {
        "scraper": {
            "scraping_mode": "",
            "period": ()
        },
        "igram_dicts": {}
    }

    scraping_mode = config.get('scraping', 'scraping_mode')

    since_ts = 0
    until_ts = datetime.timestamp(datetime.now())

    config_since = config.get('period', 'since')
    config_until = config.get('period', 'until')

    if config_since:
        since_ts = datetime.timestamp(
            datetime.strptime(config_since, "%Y-%m-%d"))
    if config_until:
        until_ts = datetime.timestamp(
            datetime.strptime(config_until, "%Y-%m-%d"))

    create_accounts_dict = config.getboolean("create_dictionaries", "accounts")
    create_posts_dict = config.getboolean("create_dictionaries", 'posts')
    number_of_posts = config.getint("create_dictionaries", 'number_of_posts')

    settings = {
        "scraper": {
            "scraping_mode": scraping_mode,
            "period": (since_ts, until_ts)
        },
        "igram_dicts": {
            "create_accounts_dict": create_accounts_dict,
            "create_posts_dict": create_posts_dict,
            "number_of_posts": number_of_posts
        }
    }

    return settings


def main():

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    config = read_config()
    print(f"Loaded config at {(strftime('%X %x'))}")

    if (config["igram_dicts"]["create_posts_dict"] or config["igram_dicts"]["create_accounts_dict"]):

        igram_dicts.main(timestamp, **config["igram_dicts"])

    scraper.main(timestamp, **config["scraper"])


if __name__ == '__main__':
    main()
