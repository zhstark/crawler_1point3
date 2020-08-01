# Spider:
import scrapy
import pymongo
import datetime
import re
from crawler_1point3.items import Crawler1Point3Item

class Spider1point3(scrapy.Spider):
    name = "Spider1point3"
    reach_last = False
    date_exp = r'[0-9]*\-[0-9]*\-[0-9]*'
    url_frame = ['https://www.1point3acres.com/bbs/forum-28-', '.html']
    page_number = 1

    def __init__(self, mongo_uri='mongodb://localhost:27017/', mongo_db='cralwer_1point3', page_range=10):
        """
        access the database to get the last work date from collection 'spider_work_date', if no such collection, default 10 years ago.
        """
        self.page_range = page_range
        client = pymongo.MongoClient(mongo_uri)
        db = client[mongo_db]
        # default ending date: 10 years ago
        self.last_date = (datetime.datetime.today() - datetime.timedelta(days=10*365)).strftime('%Y-%m-%d')
        for t in db['spider_work_date'].find().sort('date', -1):
            self.last_date = t['date']
            if re.match(r'[0-9]*\-[0-9]*\-[0-9]*', self.last_date):
                break
        self.logger.info('LAST DATE: '+ self.last_date)
        self.today = datetime.datetime.today()
        client.close()

    @classmethod
    def from_crawler(cls, crawler):
        mongo_uri=crawler.settings.get('MONGO_URI')
        mongo_db=crawler.settings.get('MONGO_DATABASE', 'cralwer_1point3')
        page_range = crawler.settings.get('PAGE_RANGE', 10)
        return cls(mongo_uri, mongo_db, page_range)

    def start_requests(self):
        yield scrapy.Request('https://www.1point3acres.com/bbs/forum-28-1.html', self.parse)

    def parse(self, response):
        """
        transfer all posts into items with keys:
            title
            company
            author
            create_date: string, %Y-%m-%d
            last_reply_date: string, %Y-%m-%d
        and pass the item to pipeline
        in order to not do duplicated work, if current post date is eailer than the last work date, set self.reach_last true
        """
        self.logger.debug('parsing')
        self.logger.debug('Current page number is %d', self.page_number)
        path_to_post = ['div.wp div.boardnav div.mn div.tl div.bm_c', '//table[@id="threadlisttableid"]/tbody[contains(@id, "normalthread")]']

        for post in response.css(path_to_post[0]).xpath(path_to_post[1]):
            item = self.extract_info(post)
            if item == None:
                continue    
            yield item
        
        if self.reach_last is False and self.page_number < self.page_range:
            self.page_number += 1
            url = self.url_frame[0]+str(self.page_number)+self.url_frame[1]
            yield scrapy.Request(url=url, callback=self.parse)



    def extract_info(self, post):
        # new reply post vs no-new-reply post
        path_to_th = ['th.new', 'th.common']
        path_to_title = 'a.s::text'
        path_to_company = 'span span u b font::text'
        path_to_time = 'td.by em span::text'
        path_to_author = 'td.by cite a::text'
        
        item = Crawler1Point3Item()
        th = post.css(path_to_th[0])
        if th == []:
            th = post.css(path_to_th[1])
        if th == []:
            return None

        # get company at index 1 e.g: [ full-time, Google]
        job_company = th.css(path_to_company).getall()
        # get post title
        title = th.css(path_to_title).get()
        # get create time at index 0
        time = post.css(path_to_time).getall()
        # get author (0) and newest replier (1)
        by = post.css(path_to_author).getall()
        # may not have company
        if len(job_company) > 1:
            item["company"] = job_company[1]

        item["title"] = title
        item["create_date"] =  self.get_create_date(time[0])
        if len(time) > 1:
            item['last_reply_date'] = self.get_create_date(time[1])
        else:
            item['last_reply_date'] = self.get_create_date(post.css('td.by em a::text').get())
        # may anonymous author
        if len(by) > 1:
            item["author"] = by[0]            
        #self.logger.info("Get item \n %s", item)
        if not self.reach_last:
            self.reach_last = self.has_reached_lasttime(item)
        return item

    def get_create_date(self, time):
        """
        process time with format like '5 天前' to date format like '2020-3-3'
        
        :return: string with format %Y-%m-%d
        """
        # if empty, return empty
        if time == "":
            return ""
        # already in good format, change 2020-7-7 to 2020-07-07
        match = re.match(self.date_exp, time)
        if match:
            return datetime.datetime.strptime(match.group(0),'%Y-%m-%d').strftime('%Y-%m-%d')
        
        # others like:  "5 天前", "昨天 06:16", "5 小时前", "前天 05:23", "5 分钟前", 
        time_list = time.split('\xa0')
        if len(time_list) == 2:
            if self.is_number(time_list[0]):
                num = int(time_list[0])
                unit = time_list[1][:-1]
                if unit == "天":
                    return (self.today - datetime.timedelta(days=num)).strftime('%Y-%m-%d')
                elif unit == "小时":
                    return (self.today - datetime.timedelta(hours=num)).strftime('%Y-%m-%d')
                elif unit == "分钟":
                    return (self.today - datetime.timedelta(minutes=num)).strftime('%Y-%m-%d')
                elif unit == '秒':
                    return (self.today - datetime.timedelta(milliseconds=num)).strftime('%Y-%m-%d')
            elif time_list[0] == "昨天":
                return (self.today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            elif time_list[0] == "前天":
                return (self.today - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        elif time_list[0] == "半小时前":
            return (self.today - datetime.timedelta(minutes=30)).strftime('%Y-%m-%d')

        # unknow format
        return time

    def has_reached_lasttime(self, item):
        if 'last_reply_date' in item and re.match(self.date_exp, item['last_reply_date']):
            return item['last_reply_date'] < self.last_date
        return False

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            pass
        
        return False

