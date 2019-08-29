import argparse
import datetime
import feedparser
import time
import yaml
from multiprocessing import Pool
from pymongo import MongoClient


def get_formatted_time():
    local_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
    return local_time.strftime("%y-%m-%d %H:%M:%S")


class RSS:
    def __init__(self, rss_name: str, rss_link: str, rss_keys_list: list, database):
        self.wait_time = 1
        self.rss_name = rss_name
        self.rss_link = rss_link
        self.rss_keys_list = rss_keys_list
        self.database = database

    def fetch_and_save_rss(self):

        rss = feedparser.parse(self.rss_link)

        for raw_item in rss.entries:
            save_item = dict((key, raw_item[key]) for key in self.rss_keys_list)
            save_item["_id"] = raw_item["link"]
            save_item["last_update_time"] = get_formatted_time()
            save_item = dict(sorted(save_item.items()))

            update_result = self.database[rss_name].update_one({'_id': save_item['_id']}, {"$set": save_item}, upsert=True)
            if update_result.matched_count == 0:
                print(get_formatted_time(), "Add new item, source :", rss_name,
                      ", item:", save_item["title"], save_item["link"])


if __name__ == "__main__":

    with open("config.yml", 'r') as ymlfile:
        config = yaml.load(ymlfile, Loader=yaml.SafeLoader)
    for rss_name in config["rss"].keys():
        config["rss"][rss_name]["link"].replace("https://rsshub.app", config["rsshub"]["host"])
        # print(config["rss"][rss_name]["link"])
    config = dict(sorted(config.items()))
    # print(config)

    parser = argparse.ArgumentParser()
    parser.add_argument("--mongodb_host", default=None, type=str,
                        help="the link of mongoDB, example: localhost:27017")
    parser.add_argument("--rsshub_host", default=None, type=str,
                        help="the host of RSSHub with http or https, example: https://rsshub.app http://localhost:1200")
    args = parser.parse_args()

    if args.mongodb_host is not None:
        config['mongodb']['link'] = args.mongodb_host
        print("Using mongodb_host from args, i.e. ", args.mongodb_host)
    if args.rsshub_host is not None:
        config["rsshub"]["host"] = args.rsshub_host
        print("Using rsshub_host from args, i.e. ", args.rsshub_host)

    db_client = MongoClient(config['mongodb']['link'])
    database = db_client["rss_spider"]

    rss_list = []
    for key, value in config["rss"].items():
        rss = RSS(key, value["link"], value["key_list"], database)
        rss_list.append(rss)

    while True:

        print(get_formatted_time(), "start")

        pool = Pool(len(rss_list))
        for rss in rss_list:
            rss.fetch_and_save_rss()
            pool.apply_async(rss.fetch_and_save_rss())
        pool.close()
        pool.join()

        # break
        print(get_formatted_time(), "end")
        time.sleep(5)

    db_client.close()