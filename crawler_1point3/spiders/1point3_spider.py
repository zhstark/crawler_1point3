import scrapy
from crawler_1point3.items import Crawler1Point3Item

class Spider1point3(scrapy.Spider):
    name = "Spider1point3"

    path_to_post = ['div.wp div.boardnav div.mn div.tl div.bm_c', '//table[@id="threadlisttableid"]', 'tbody']
    # new post vs no-new-reply post
    path_to_th = ['th.new', 'th.common']
    path_to_title = 'a.s::text'
    path_to_company = 'span span u b font::text'
    path_to_time = 'td.by em span::text'

    def start_requests(self):
        url_frame=['https://www.1point3acres.com/bbs/forum-28-', '.html']

        # how many pages want to scrape
        last_page=10
        urls = []
        for i in range(1, last_page+1):
            urls.append(url_frame[0]+str(i)+url_frame[1])
        #urls=['https://www.1point3acres.com/bbs/forum-28-2.html']
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        self.log('I am parsing')

        for post in response.css(self.path_to_post[0]).xpath(self.path_to_post[1]).css(self.path_to_post[2]):
            
            item = Crawler1Point3Item()
            th = post.css(self.path_to_th[0])
            if th == []:
                th = post.css(self.path_to_th[1])
            if th == []:
                continue

            # get company at index 1 e.g: [ full-time, Google]
            job_company = th.css(self.path_to_company).getall()
            # get post title
            title = th.css(self.path_to_title).get()

            # get create time at index 0
            time = post.css(self.path_to_time).getall()

            # may not have company
            if len(job_company) > 1:
                item["company"] = job_company[1]

            item["title"] = title
            item["create_date"] =  time[0]
            yield item
