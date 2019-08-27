import feedparser
import yaml
from pymongo import MongoClient


def fetch_and_save_rss(rss_name: str, rss_link: str, rss_keys_list: list, database):

    rss = feedparser.parse(rss_link)

    for raw_item in rss.entries:
        save_item = dict((key, raw_item[key]) for key in rss_keys_list)
        save_item["_id"] = raw_item["id"]
        update_result = database[rss_name].update_one({'_id': save_item['_id']}, {"$set": save_item}, upsert=True)
        if update_result.matched_count == 0:
            print("Add new item, source :", rss_name, ", item:", save_item["title"], save_item["link"])


if __name__ == "__main__":

    with open("config.yml", 'r') as ymlfile:
        config = yaml.load(ymlfile, Loader=yaml.SafeLoader)

    for rss_name in config["rss"].keys():
        config["rss"][rss_name]["link"].replace("https://rsshub.app", config["rsshub"]["host"])
        # print(config["rss"][rss_name]["link"])
    print(config)

    db_client = MongoClient(config['mongodb']['link'])
    database = db_client["rss_spider"]

    for key, value in config["rss"].items():
        fetch_and_save_rss(key, value["link"], value["key_list"], database)

    db_client.close()
