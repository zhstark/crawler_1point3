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

class Crawler1Point3Pipeline:

    company_list = {
        'Facebook': 0, 'Google': 0, 'Apple': 0, 'Airbnb': 0, 'Amazon': 0,
        'Tiktok': 0, 'Other': 0
    }

    file_name = 'item.md'
    date_exp = r'[0-9]*\-[0-9]*\-[0-9]*'
    # time range of post, unit: day
    date_range = 10

    cmd = "pandoc " + file_name + " -f markdown -t html -s -o item.html"

    def open_spider(self, spider):
        self.file = open('item.md', 'w')
        self.today = datetime.datetime.today()

    def close_spider(self, spider):
        self.write_markdown()
      #  json.dump(self.company_list, self.json_file_w)
        self.file.close()
        os.popen(self.cmd)

    def process_item(self, item, spider):
        # process new data
        adapter = ItemAdapter(item)

        # only process those have company label
        if 'company' in adapter:
            company = adapter.get('company')
            date = adapter.get('create_date')

            if self.in_time_range(date):
                if company in self.company_list:
                    self.company_list[company] += 1
                else:
                    self.company_list['Other'] += 1
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