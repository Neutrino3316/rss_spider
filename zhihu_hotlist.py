import feedparser
from pymongo import MongoClient


if __name__ == "__main__":
    db_client = MongoClient("mongodb://localhost:27023")
    database = db_client["rss_spider"]

    rss_item_keys_set = {'title', 'summary', 'published', 'link', 'author'}

    rss = feedparser.parse("https://rsshub.app/zhihu/hotlist")

    for raw_item in rss.entries:
        save_item = dict((key, raw_item[key]) for key in rss_item_keys_set)
        save_item["_id"] = raw_item["id"]
        # insert_result = database["zhihu_hotlist"].insert_one(save_item)
        update_result = database["zhihu_hotlist"].update_one({'_id': save_item['_id']}, {"$set": save_item}, upsert=True)

    db_client.close()
