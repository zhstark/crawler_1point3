#!/bin/bash
path=`pwd`
cd ${path}/crawler_1point3
#startevenv
scrapy crawl Spider1point3
cd ${path}/crawler_leetcode
scrapy crawl LeetcodeSpider