import yaml
from pymongo import MongoClient


if __name__ == "__main__":

    with open("config.yml", 'r') as ymlfile:
        config = yaml.load(ymlfile, Loader=yaml.SafeLoader)

    print(config)

    db_client = MongoClient(config['mongodb']['link'])

    db_client.close()
