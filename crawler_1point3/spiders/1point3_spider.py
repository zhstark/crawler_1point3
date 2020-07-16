import scrapy
from crawler_1point3.items import Crawler1Point3Item
import datetime

class Spider1point3(scrapy.Spider):
    name = "Spider1point3"
    
    self.curr_time = datetime.datetime.now()

    def start_requests(self):
        url_frame=['https://www.1point3acres.com/bbs/forum-28-', '.html']
        last_page=2
        urls = []
        for i in range(1, last_page+1):
            urls.append(url_frame[0]+str(i)+url_frame[1])
        #urls=['https://www.1point3acres.com/bbs/forum-28-2.html']
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        path_to_post = ['div.wp div.boardnav div.mn div.tl div.bm_c', '//table[@id="threadlisttableid"]', 'tbody']
        path_to_company = ['th.new span span u b font::text']
        path_to_create_time = ['td.by em span span::text']

        self.log('I am parsing')
        for post in response.css(path_to_post[0]).xpath(path_to_post[1]).css(path_to_post[2]):
            # item= Crawler1Point3Item(name='item', company=front)
            # yield item
            item = Crawler1Point3Item()
            #company = post.css(path_to_company)[1].get()
            item["company"] = post.css(path_to_company)[1].get()
            item["date"] = post.css(path_to_create_time).get()

            yield item
