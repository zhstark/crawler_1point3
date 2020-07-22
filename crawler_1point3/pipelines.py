# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os
import json
import datetime
import re
import pymongo


class Crawler1Point3Pipeline:

    company_list = {
        'Facebook': 0, 'Google': 0, 'Apple': 0, 'Airbnb': 0, 'Amazon': 0,
        'Tiktok': 0, 'Other': 0
    }

    file_name = 'item.md'
    date_exp = r'[0-9]*\-[0-9]*\-[0-9]*'
    collection_name = 'posts'
    # # time range of post, unit: day
    # date_range = 10

    cmd = "pandoc " + file_name + " -f markdown -t html -s -o item.html"

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
        self.file = open('item.md', 'w')
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        """
        when a spider finishs its work, write all scraped data and close the file
        """
        self.write_markdown()
      #  json.dump(self.company_list, self.json_file_w)
        self.file.close()
        os.popen(self.cmd)

        self.client.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        # make date format be %Y-%m-%d
        adapter['create_date'] = self.get_create_date(adapter['create_date'])
        # only process those have company label
        if 'company' in adapter:
            company = adapter.get('company')
            date = adapter.get('create_date')

            if self.in_time_range(date):
                if company in self.company_list:
                    self.company_list[company] += 1
                else:
                    self.company_list['Other'] += 1

        post = adapter.asdict()
        db_collection = self.db[self.collection_name]
        # if this post is new
        if db_collection.count_documents(post) == 0:
            print("GOING TO INSERT")
            db_collection.insert_one(post)
        
        #self.db[self.collection_name].insert_one(ItemAdapter(item).asdict())
        return item

    def write_markdown(self):
        unit = '| ---- '
        name_list = ""
        num_list = ""
        head = ""
        for name, num in self.company_list.items():
            head += unit
            name_list += "| " + name + " "
            num_list += "| " + str(num) + " "
        name_list += '|\n'
        num_list += '|\n'
        head += '|\n'
        self.file.write(name_list)
        self.file.write(head)
        self.file.write(num_list)

    def in_time_range(self, date):
        if re.match(self.date_exp, date):
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
            date_low_boundary = self.today - datetime.timedelta(days=self.date_range)
            if date < date_low_boundary:
                return False
        
        return True

    def get_create_date(self, time):
        """
        process time with format like '5 天前' to date format like '2020-3-3'
        
        :return: string with format %Y-%m-%d
        """
        # if empty, return empty
        if time == "":
            return ""
        # already in good format
        if re.match(self.date_exp, time):
            return time
        
        # others like:  "5 天前", "昨天 06:16", "5 小时前", "前天 05:23", "5 分钟前", 
        time = time.split('\xa0')
        if len(time) == 2:
            if self.is_number(time[0]):
                num = int(time[0])
                unit = time[1][:-1]
                if unit == "天":
                    return (self.today - datetime.timedelta(days=num)).strftime('%Y-%m-%d')
                elif unit == "小时":
                    return (self.today - datetime.timedelta(hours=num)).strftime('%Y-%m-%d')
                else:
                    return self.today.strftime('%Y-%m-%d')
            elif time[0] == "昨天":
                return (self.today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            elif time[0] == "前天":
                return (self.today - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        
        # unknow format
        return time

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            pass
        
        return False