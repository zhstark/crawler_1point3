# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymongo
import logging


class CrawlerLeetcodePipeline:

    def __init__(self, mongo_url="", mongo_db="", date_range=""):
        self.mongo_url = mongo_url
        self.mongo_db = mongo_db
        self.date_range = date_range
        self.client = pymongo.MongoClient(self.mongo_url)
        self.db = self.client[self.mongo_db]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_url=crawler.settings.get('MONGO_URL'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items'),
            date_range=crawler.settings.get('DATE_RANGE', 10)
        )
    
    def __del__(self):
        self.client.close()


    def process_item(self, item, spider):
        post = ItemAdapter(item).asdict()
        collection = self.db['interview_questions']
        if collection.count_documents(post) == 0:
            logging.debug("Insert a new item")
            collection.insert_one(post)
        return item
