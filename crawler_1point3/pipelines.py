# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os
import json

class Crawler1Point3Pipeline:

    company_list = {
        'Facebook': 0, 'Google': 0, 'Apple': 0, 'Airbnb': 0, 'Amazon': 0,
        'Tiktok': 0
    }

    file_name = 'item.md'

    cmd = "pandoc " + file_name + " -f markdown -t html -s -o item.html"

    def open_spider(self, spider):
        self.json_file_w = open('item.json', 'w')
        self.json_file_r = open('item.json', 'r')
        self.file = open('item.md', 'w')

        # read old data
        old_data = self.json_file_r.read()
        if old_data != "":
            old_data=json.loads(old_data)
            for k, v in old_data.items():
                self.company_list[k]+=int(v)
                
        print('I get old data: ' + json.dumps(self.company_list))

    def close_spider(self, spider):
        self.writeMarkdown()
        json.dump(self.company_list, self.json_file_w)
        self.file.close()
        self.json_file_w.close()
        self.json_file_r.close()
        os.popen(self.cmd)

    def process_item(self, item, spider):
        # process new data
        adapter = ItemAdapter(item)
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
