# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Crawler1Point3Item(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    post = scrapy.Field()

    title = scrapy.Field()
    company = scrapy.Field()
    author = scrapy.Field()
    create_date = scrapy.Field()
    last_reply_date = scrapy.Field()

    # extra info for interview posts
    position = scrapy.Field()
    interview_type = scrapy.Field()
    apply_method = scrapy.Field()
