# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os
import json
import datetime

class Crawler1Point3Pipeline:

    company_list = {
        'Facebook': 0, 'Google': 0, 'Apple': 0, 'Airbnb': 0, 'Amazon': 0,
        'Tiktok': 0
    }

    file_name = 'item.md'

    cmd = "pandoc " + file_name + " -f markdown -t html -s -o item.html"

    def open_spider(self, spider):
        self.file = open('item.md', 'w')

    def close_spider(self, spider):
        self.writeMarkdown()
      #  json.dump(self.company_list, self.json_file_w)
        self.file.close()
        os.popen(self.cmd)

    def process_item(self, item, spider):
        # process new data
        adapter = ItemAdapter(item)

        # only process those have company
        if 'company' in adapter:
            data = adapter.get('company')
            if data in self.company_list:
                self.company_list[data] += 1

        return item

    def writeMarkdown(self):
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
