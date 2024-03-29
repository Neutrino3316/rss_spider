import argparse
import datetime
import dateutil.parser
import feedparser
import logging
import time
import yaml
from multiprocessing import Pool
from pymongo import MongoClient

# set logging format and logging level
# logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)
logging.basicConfig(format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d PID:%(process)d %(name)s \t %(message)s",
                    level=logging.DEBUG)

# set time format
strftime_time_formatted = {
    "with_time_zone": "%y-%m-%d %H:%M:%S %Z",
    "without_time_zone": "%y-%m-%d %H:%M:%S %Z"}


def get_time_now():
    local_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    local_time = local_time.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
    return local_time.strftime(strftime_time_formatted["with_time_zone"])


class RSS:
    """
    A listener of one rss source
    """
    def __init__(self, rss_name: str, rss_link: str, rss_keys_list: list, database_link, database_name: str):
        # the rss information, including the name, the link address, the key list.
        self.rss_name = rss_name
        self.rss_link = rss_link
        self.rss_keys_list = rss_keys_list

        # the database information, the data fetch from the rss will be stored in this database
        self.database_link = database_link
        self.database_name = database_name

        self.log_tag = "rss %s\t" % self.rss_name
        self.rss = None  # the rss object returned by the feedparser
        self.new_items_count = 0  # how many new items found in the latest fetch compared to the penultimate one.
        self.save_item_list = []  # the key of the items need to be fetched and saved
        self.waiting_time = 1  # initial waiting time between each data fetch, the time unit is second

    #     self._create_logger()
    #     # self.logger.warning("This rss has created.")
    #
    # def _create_logger(self):
    #     self.logger = logging.getLogger("rss:%s\t" % self.rss_name)
    #     self.logger.setLevel(logging.DEBUG)
    #     self.logger.info("Logger created.")

    def fetch(self):
        """
        Fetch the rss. Using the self.rss_link. Data fetched will be stored in a rss object, in self.rss
        :return: None
        """
        self.rss = feedparser.parse(self.rss_link)

    def parse_item(self):
        """
        Using the data fetched in self.rss, parse the data and store them in self.save_item_list
        :return:
        """
        self.save_item_list = []
        for raw_item in self.rss.entries:
            save_item = dict((key, raw_item[key]) for key in self.rss_keys_list)
            save_item["_id"] = raw_item["link"]
            save_item["last_update_time"] = get_time_now()
            # save_item["published_parsed"] = RSS.parse_time(save_item.pop("published"))
            save_item["published_parsed"] = RSS.parse_time(save_item["published"])
            save_item = dict(sorted(save_item.items()))
            self.save_item_list.append(save_item)

    @staticmethod
    def parse_time(raw_time_string):
        """
        Parse the time string
        :param raw_time_string: a string of time
        :return: a class datetime.datetime object
        """
        return dateutil.parser.parse(raw_time_string)

    def save_item(self):
        """
        Save the new items into the database
        Store the amount of new items in self.new_items_count
        Start and close a connection to the database
        :return: None
        """
        self.new_items_count = 0
        db_client = MongoClient(self.database_link)
        database = db_client[self.database_name]
        for save_item in self.save_item_list:
            update_result = database[self.rss_name].update_one({'_id': save_item['_id']}, {"$set": save_item},
                                                               upsert=True)
            if update_result.matched_count == 0:
                self.new_items_count += 1
                logging.info(self.log_tag + "Add new item:\n%s\n%s" % (save_item["title"], save_item["link"]))
        db_client.close()

    def update_waiting_time(self):
        """
        Algorithm of updating the waiting time, i.e. self.waiting_time
        Double the waiting time if no new items are found in the latest fetch.
        Cut the waiting time in half if more than 5 new items are found in the latest fetch.
        :return: None
        """
        if self.new_items_count == 0:
            self.waiting_time *= 2
            # self.logger.info("Waiting time doubled, the new waiting time is %d seconds" % self.waiting_time)
            logging.info(self.log_tag + "Waiting time doubled, the new waiting time is %d seconds." % self.waiting_time)
        elif self.new_items_count > 5:
            self.waiting_time /= 2
            # self.logger.info("Waiting time cut in half, the new waiting time is %d seconds" % self.waiting_time)
            logging.info(self.log_tag + "Waiting time cut in half, the new waiting time is %d seconds." % self.waiting_time)

    def run(self):
        """
        Start a dead loop. It will fetch and save the data continuously.
        :return: None
        """
        while True:
            # self.logger.info("Start now.")
            logging.info(self.log_tag + "Start a new round.")
            self.fetch()
            self.parse_item()
            self.save_item()
            self.update_waiting_time()
            # self.logger.info("start end, will waiting %d seconds before next run" % self.waiting_time)
            logging.info(self.log_tag + "End this round, will wait %d seconds before next round." % self.waiting_time)
            time.sleep(self.waiting_time)


if __name__ == "__main__":

    # create root logger
    logger = logging.getLogger("main")
    logger.setLevel(logging.DEBUG)

    logger.warning("The initial of this program, everything will load and start in a minute.")

    # read config.yml
    with open("config.yml", 'r') as ymlfile:
        config = yaml.load(ymlfile, Loader=yaml.SafeLoader)
    logger.info("Config loaded: %s" % config)

    # parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongodb_host", default=None, type=str,
                        help="the link of mongoDB, e.g. localhost:27017， mongo_rss_spider:27017")
    parser.add_argument("--rsshub_host", default=None, type=str,
                        help="the host of RSSHub with http or https, e.g. \
                        https://rsshub.app http://localhost:1200 http://rsshub_diygod:1200")
    parser.add_argument("--test", action="store_true",
                        help="if test, write data to database named rss_spider_test.")
    args = parser.parse_args()

    # override the mongodb_host and the rsshub_host if the corresponding argument is passed.
    logger.info("Arguments loaded: %s" % args)
    if args.mongodb_host is not None:
        config['mongodb']['link'] = args.mongodb_host
        logger.info("Using mongodb_host from args, i.e. %s" % args.mongodb_host)
    if args.rsshub_host is not None:
        config["rsshub"]["host"] = args.rsshub_host
        logger.info("Using rsshub_host from args, i.e. %s" % args.rsshub_host)

    # whether to save the data in test database or not
    if args.test:
        database_name = "rss_spider_test"
    else:
        database_name = "rss_spider"

    # for every rss, replace host name and sort items
    for rss_name in config["rss"].keys():
        config["rss"][rss_name]["link"] = config["rss"][rss_name]["link"].replace(
            "rsshub_host", config["rsshub"]["host"])
    config = dict(sorted(config.items()))

    # create a rss_list that include all rss
    rss_list = []
    for key, value in config["rss"].items():
        rss = RSS(key, value["link"], value["key_list"], config['mongodb']['link'], database_name)
        rss_list.append(rss)

    # print the number of rss loaded and all rss details
    logger.info("%d rss are loaded. They're list as the followings:" % len(rss_list))
    for i, rss in enumerate(rss_list):
        logger.info("%d/%d rss name: %s \t link: %s" % (i+1, len(rss_list), rss.rss_name, rss.rss_link))

    # use multiprocessing, for each rss, create a process that continuously fetch, parse and store data
    logger.warning("Start all rss. Each rss has a unique thread to fetch parse and store the data.")
    pool = Pool(len(rss_list))
    for i in range(len(rss_list)):
        pool.apply_async(rss_list[i].run)
    pool.close()
    pool.join()

    # should never be run
    logger.error("All ended!")
