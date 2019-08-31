import argparse
import datetime
import feedparser
import threading
import time
import yaml
from multiprocessing import Pool
from pymongo import MongoClient


def get_formatted_time():
    local_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
    return local_time.strftime("%y-%m-%d %H:%M:%S")


class RSS:
    def __init__(self, rss_name: str, rss_link: str, rss_keys_list: list, database_link):
        self.wait_time = 1
        self.rss_name = rss_name
        self.rss_link = rss_link
        self.rss_keys_list = rss_keys_list
        self.database_link = database_link

        self.rss = None
        self.new_items_count = 0
        self.save_item_list = []

    def fetch(self):
        self.rss = feedparser.parse(self.rss_link)

    def parse_item(self):
        self.save_item_list = []
        for raw_item in self.rss.entries:
            save_item = dict((key, raw_item[key]) for key in self.rss_keys_list)
            save_item["_id"] = raw_item["link"]
            save_item["last_update_time"] = get_formatted_time()
            save_item = dict(sorted(save_item.items()))
            self.save_item_list.append(save_item)

    def save_item(self):
        self.new_items_count = 0
        db_client = MongoClient(self.database_link)
        database = db_client["rss_spider"]
        for save_item in self.save_item_list:
            update_result = database[self.rss_name].update_one({'_id': save_item['_id']}, {"$set": save_item}, upsert=True)
            if update_result.matched_count == 0:
                self.new_items_count += 1
                print(get_formatted_time(), "Add new item, source :", self.rss_name,
                      ", item:", save_item["title"], save_item["link"])
        db_client.close()

    def update_wait_time(self):
        if self.new_items_count == 0:
            self.wait_time *= 2
        elif self.new_items_count > 5:
            self.wait_time /= 2

    def run(self):
        while True:
            print(get_formatted_time(), self.rss_name, "start, wait time is:", self.wait_time)
            self.fetch()
            self.parse_item()
            self.save_item()
            self.update_wait_time()
            print(get_formatted_time(), self.rss_name, "end")
            time.sleep(self.wait_time)


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

    rss_list = []
    for key, value in config["rss"].items():
        rss = RSS(key, value["link"], value["key_list"], config['mongodb']['link'])
        rss_list.append(rss)

    print(get_formatted_time(), "all start")
    print(len(rss_list))
    for rss in rss_list:
        print(rss.rss_name)

    # thread_list = []
    # for rss in rss_list:
    #     thread = threading.Thread(target=rss.run)
    #     thread_list.append(thread)
    # for thread in thread_list:
    #     thread.start()

    pool = Pool(len(rss_list))
    for i in range(len(rss_list)):
        pool.apply_async(rss_list[i].run)
    pool.close()
    pool.join()

    print(get_formatted_time(), "all end")
