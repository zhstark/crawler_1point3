# Define your item pipelines here
# All posts are delivered to this pipeline as items.
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os
import json
import datetime
import re
import pymongo
import logging


class Crawler1Point3Pipeline:
    
    collection_name = 'posts'

    # used for local test
    company_list = {"Apple": 0, "Facebook": 0, "Google": 0}

    def __init__(self, mongo_uri="", mongo_db="", date_range=""):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.date_range = date_range
        self.today = datetime.datetime.today()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items'),
            date_range=crawler.settings.get('DATE_RANGE', 10)
        )

    def open_spider(self, spider):
        """
        when a spider begins to work, open a file to write the scraped data and get the current time.
        """
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        """
        when a spider finishs its work, 
        1. record work date in collection spider_work_date
        2. write all scraped data and close the file
        """
        collection = self.db['spider_work_date']
        collection.insert_one({'date': self.today.strftime('%Y-%m-%d') })
        # self.create_forms_by_db()
        self.client.close()

    def process_item(self, item, spider):
        """
        given an item of post, this function:
        1. for each post, get rid of 'last_reply_date' key to see if this post has been stored before
        2. update/insert the post
        """
        adapter = ItemAdapter(item)
        post = adapter.asdict()
        # get rid of ‘last_reply_date’ key
        last_reply_date = ''
        if 'last_reply_date' in post:
            last_reply_date = post['last_reply_date']
            post.pop('last_reply_date')
        db_collection = self.db[self.collection_name]
        #logging.debug("search for post: \n %s", post)
        # if this post is new, insert the origin post
        if db_collection.count_documents(post) == 0:
            logging.debug("Insert a new item")
            db_collection.insert_one(adapter.asdict())
        # this post has been stored before, update 
        else:
            if last_reply_date != '':
                logging.debug("Updating an item %s", last_reply_date)
                db_collection.update_one(post, { "$set": { "last_reply_date": last_reply_date } })
        
        return item

    def write_markdown(self, f, dic):
        """
        :param f: the file that you want to write
        :param dic: a dictionary where the data comes from
        """
        unit = '| ---- '
        name_list = ""
        num_list = ""
        head = ""
        for name, num in dic.items():
            head += unit
            name_list += "| " + name + " "
            num_list += "| " + str(num) + " "
        name_list += '|\n'
        num_list += '|\n'
        head += '|\n'
        f.write(name_list)
        f.write(head)
        f.write(num_list)


    # used for test
    def create_forms_by_db(self):
        """
        create forms according to the data in database
        """
        f = open('data.md', 'w')
        db_collection = self.db[self.collection_name]
        for delta in range(0, self.date_range+1):
            date = (self.today - datetime.timedelta(days=delta)).strftime('%Y-%m-%d')
            s = "## Date: "+ date + '\n'
            f.write(s)
            f.write('\n')
            table = {}
            for company in self.company_list.keys():
                posts = {'company': company, 'create_date': date}
                count = db_collection.count_documents(posts)
                self.company_list[company] += count
                table[company] = count
            self.write_markdown(f, table)
            f.write('\n')
            f.write('\n')

        f.write("## Recent 10 days: \n")
        self.write_markdown(f, self.company_list)
        f.close()

