# -*- coding: utf-8 -*-
# Spider:
import scrapy
import pymongo
import datetime
import re
from crawler_1point3.items import Crawler1Point3Item

class Spider1point3(scrapy.Spider):
    name = "Spider1point3"
    jobs_reach_last = False
    interviews_reach_last = False
    date_exp = r'[0-9]*\-[0-9]*\-[0-9]*'
    path_to_post = ['div.wp div.boardnav div.mn div.tl div.bm_c', '//table[@id="threadlisttableid"]/tbody[contains(@id, "normalthread")]']
    jobs_page_number = 1
    interviews_page_number = 1

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
        """
            get setting configuration
            return to instance initialization
        """
        mongo_uri=crawler.settings.get('MONGO_URI')
        mongo_db=crawler.settings.get('MONGO_DATABASE', 'cralwer_1point3')
        page_range = crawler.settings.get('PAGE_RANGE', 10)
        return cls(mongo_uri, mongo_db, page_range)

    def start_requests(self):
        jobs_url = "https://www.1point3acres.com/bbs/forum-28-1.html"
        interviews_url = "https://www.1point3acres.com/bbs/forum-145-1.html"
        yield scrapy.Request(jobs_url, self.parse_for_jobs_post)
        yield scrapy.Request(interviews_url, self.parse_for_interviews_post)

    def parse_for_jobs_post(self, response):
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
        self.logger.debug('Currently parsing jobs page, page number is %d', self.jobs_page_number)
        url_frame = ['https://www.1point3acres.com/bbs/forum-28-', '.html']
        # parsing current page
        for post in response.css(self.path_to_post[0]).xpath(self.path_to_post[1]):
            item = self.extract_common_info(post)
            if item == None:
                continue   
            item["post"] = "jobs"
            self.extract_info_for_jobs(post, item)
            if not self.jobs_reach_last:
                self.jobs_reach_last = self.has_reached_lasttime(item)
            yield item
        # generate next page 
        if self.jobs_reach_last is False and self.jobs_page_number < self.page_range:
            self.jobs_page_number += 1
            url = url_frame[0]+str(self.jobs_page_number)+url_frame[1]
            yield scrapy.Request(url=url, callback=self.parse_for_jobs_post)

    def parse_for_interviews_post(self, response):
        self.logger.debug('Currently parsing interviews page, page number is %d', self.interviews_page_number)
        url_frame = ['https://www.1point3acres.com/bbs/forum-145-', '.html']

        for post in response.css(self.path_to_post[0]).xpath(self.path_to_post[1]):
            item = self.extract_common_info(post)
            if item == None:
                continue   
            item["post"] = "interviews"
            self.extract_infor_for_interviews(post, item)
            if not self.interviews_reach_last:
                self.interviews_reach_last = self.has_reached_lasttime(item)
            yield item

        if self.interviews_reach_last is False and self.interviews_page_number < self.page_range:
            self.interviews_page_number += 1
            url = url_frame[0]+str(self.interviews_page_number)+url_frame[1]
            yield scrapy.Request(url=url, callback=self.parse_for_interviews_post)

    def extract_common_info(self, post):
        """
            extract info which exist same way in both interview posts and jobs post
            including: title, create_date, last_reply_date, author
            return: Crawler1Point3Item()
        """
        # new reply post vs no-new-reply post
        path_to_th = ['th.new', 'th.common']
        path_to_title = 'a.s::text'
        path_to_time = 'td.by em span::text'
        path_to_author = 'td.by cite a::text'

        item = Crawler1Point3Item()
        th = post.css(path_to_th[0])
        if th == []:
            th = post.css(path_to_th[1])
        if th == []:
            return None

        title = th.css(path_to_title).get()
        # get create time at index 0
        time = post.css(path_to_time).getall()
        # get author (0) and newest replier (1)
        by = post.css(path_to_author).getall()

        item["title"] = title
        item["create_date"] =  self.get_create_date(time[0])
        if len(time) > 1:
            item['last_reply_date'] = self.get_create_date(time[1])
        else:
            item['last_reply_date'] = self.get_create_date(post.css('td.by em a::text').get())
        # may anonymous author
        if len(by) > 1:
            item["author"] = by[0]            

        return item

    def extract_info_for_jobs(self, post, item):
        """
            for jobs post, extract company
        """
        path_to_th = ['th.new', 'th.common']
        th = post.css(path_to_th[0])
        if th == []:
            th = post.css(path_to_th[1])
        path_to_company = 'span span u b font::text'
        job_company = th.css(path_to_company).getall()
        if len(job_company) > 1:
            item["company"] = job_company[1]

    def extract_infor_for_interviews(self, post, item):
        """
            for interview post, extract:
                company, apply_method, interview_type, position
        """
        path_to_th = ['th.new', 'th.common']
        th = post.css(path_to_th[0])
        if th == []:
            th = post.css(path_to_th[1])
        # get company
        path_to_company = 'span u b font[color="#FF6600"]::text'
        item["company"] = th.css(path_to_company).get()
        # get position 实习 vs 全职
        path_to_position = 'span b font[color="#00B2E8"]::text'
        item["position"] = th.css(path_to_position).get()
        # get apply method
        for s in th.css('span::text').getall():
            if len(s) > 6 and s[:3] == ' - ' and s[-3:] == ' - ':
                item["apply_method"] = s[3:-3]
                break
        # get interview type
        path_to_interview_type = 'span b font[color="brown"]::text'
        item["interview_type"] = th.css(path_to_interview_type).get()


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
