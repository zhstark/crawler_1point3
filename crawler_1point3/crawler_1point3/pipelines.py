# Define your item pipelines here
# All posts are delivered to this pipeline as items.
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# -*- coding: utf-8 -*-


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os
import json
import datetime
import re
import pymongo
import logging


class Crawler1Point3Pipeline:
    
    # used for local test
    company_list = {"Apple": 0, "Facebook": 0, "Google": 0}

    def __init__(self, mongo_url="", mongo_db="", date_range=""):
        self.mongo_url = mongo_url
        self.mongo_db = mongo_db
        self.date_range = date_range
        self.today = datetime.datetime.today()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_url=crawler.settings.get('MONGO_URL'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items'),
            date_range=crawler.settings.get('DATE_RANGE', 10)
        )

    def open_spider(self, spider):
        """
        """
        self.client = pymongo.MongoClient(self.mongo_url)
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
        if item['post'] == 'jobs':
            self.process_item_helper(item, "jobs")
        elif item['post'] == 'interviews':
            self.process_item_helper(item, "interviews")
        return item

    def process_item_helper(self, item, collection_name):
        """
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
        db_collection = self.db[collection_name]
        #logging.debug("search for post: \n %s", post)
        # if this post is new, insert the origin post
        if db_collection.count_documents(post) == 0:
            logging.debug("Insert a new item")
            db_collection.insert_one(adapter.asdict())
        # this post has been stored before, update 
        else:
            if last_reply_date != '':
                logging.debug("Updating an item with last_reply_date %s", last_reply_date)
                db_collection.update_one(post, { "$set": { "last_reply_date": last_reply_date } })

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
        collection_name = "jobs"
        db_collection = self.db[collection_name]
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

