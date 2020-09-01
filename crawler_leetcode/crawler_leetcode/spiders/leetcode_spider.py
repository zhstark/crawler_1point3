import scrapy
import pymongo
import datetime
import re
import time
from crawler_leetcode.items import CrawlerLeetcodeItem
import crawler_leetcode.company_list as cpl
from itemadapter import ItemAdapter

class LeetcodeSpider(scrapy.Spider):
    name = "LeetcodeSpider"

    # companies
    companies = cpl.get_companies()

    # reach the date that the crawler reached last time.
    # when it is true, no need to crawler the next page.
    reach_last_date = False
    # use a counter in case some idiots post multiple times 
    reach_last_date_counter = 0
    page = 1

    def __init__(self, mongo_uri='mongodb://localhost:27017/', mongo_db='cralwer_1point3', page_range=10):
        """
            access the database to get the last work date from collection 'spider_work_date', 
            if no such collection, default 10 years ago.
        """
        self.page_range = page_range
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[mongo_db]

    @classmethod
    def from_crawler(cls, crawler):
        """
            get setting configuration
            return to instance initialization
        """
        mongo_uri=crawler.settings.get('MONGO_URI', 'mongodb://localhost:27017/')
        mongo_db=crawler.settings.get('MONGO_DATABASE', 'cralwer_leetcode')
        page_range = crawler.settings.get('PAGE_RANGE', 10)
        return cls(mongo_uri, mongo_db, page_range)

    def  __del__(self):
        self.client.close()

    def start_requests(self):
        self.url = "https://leetcode.com/graphql"

        self.payload_frame = [
            "{\"operationName\":\"categoryTopicList\",\"variables\":{\"orderBy\":\"newest_to_oldest\",\"query\":\"\",\"skip\":",
            ",\"first\":15,\"tags\":[],\"categories\":[\"interview-question\"]},\"query\":\"query categoryTopicList($categories: [String!]!, $first: Int!, $orderBy: TopicSortingOption, $skip: Int, $query: String, $tags: [String!]) {\\n  categoryTopicList(categories: $categories, orderBy: $orderBy, skip: $skip, query: $query, first: $first, tags: $tags) {\\n    ...TopicsList\\n    __typename\\n  }\\n}\\n\\nfragment TopicsList on TopicConnection {\\n  totalNum\\n  edges {\\n    node {\\n      id\\n      title\\n      commentCount\\n      viewCount\\n      pinned\\n      tags {\\n        name\\n        slug\\n        __typename\\n      }\\n      post {\\n        id\\n        voteCount\\n        creationDate\\n        author {\\n          username\\n          isActive\\n          profile {\\n            userSlug\\n            userAvatar\\n            __typename\\n          }\\n          __typename\\n        }\\n        status\\n        coinRewards {\\n          ...CoinReward\\n          __typename\\n        }\\n        __typename\\n      }\\n      lastComment {\\n        id\\n        post {\\n          id\\n          author {\\n            isActive\\n            username\\n            profile {\\n              userSlug\\n              __typename\\n            }\\n            __typename\\n          }\\n          peek\\n          creationDate\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    cursor\\n    __typename\\n  }\\n  __typename\\n}\\n\\nfragment CoinReward on ScoreNode {\\n  id\\n  score\\n  description\\n  date\\n  __typename\\n}\\n\"}"
        ]
        payload = self.payload_frame[0]+str(15*(self.page-1))+self.payload_frame[1]
        #payload = "{\"operationName\":\"categoryTopicList\",\"variables\":{\"orderBy\":\"newest_to_oldest\",\"query\":\"\",\"skip\":0,\"first\":15,\"tags\":[],\"categories\":[\"interview-question\"]},\"query\":\"query categoryTopicList($categories: [String!]!, $first: Int!, $orderBy: TopicSortingOption, $skip: Int, $query: String, $tags: [String!]) {\\n  categoryTopicList(categories: $categories, orderBy: $orderBy, skip: $skip, query: $query, first: $first, tags: $tags) {\\n    ...TopicsList\\n    __typename\\n  }\\n}\\n\\nfragment TopicsList on TopicConnection {\\n  totalNum\\n  edges {\\n    node {\\n      id\\n      title\\n      commentCount\\n      viewCount\\n      pinned\\n      tags {\\n        name\\n        slug\\n        __typename\\n      }\\n      post {\\n        id\\n        voteCount\\n        creationDate\\n        author {\\n          username\\n          isActive\\n          profile {\\n            userSlug\\n            userAvatar\\n            __typename\\n          }\\n          __typename\\n        }\\n        status\\n        coinRewards {\\n          ...CoinReward\\n          __typename\\n        }\\n        __typename\\n      }\\n      lastComment {\\n        id\\n        post {\\n          id\\n          author {\\n            isActive\\n            username\\n            profile {\\n              userSlug\\n              __typename\\n            }\\n            __typename\\n          }\\n          peek\\n          creationDate\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    cursor\\n    __typename\\n  }\\n  __typename\\n}\\n\\nfragment CoinReward on ScoreNode {\\n  id\\n  score\\n  description\\n  date\\n  __typename\\n}\\n\"}"
        self.headers = {
            'Content-Type': 'application/json',
            'Cookie': '__cfduid=d87fabc87707ee818a9f27ea8aae0d44e1597172313; csrftoken=32odlKMzQOtMySpxGQDbTzVpC9L1ISoZstDvlCEjcD5kgh5kKfYO86AyBFOPOlq1'
        }

        yield scrapy.Request(url=self.url, callback=self.parse, method="POST", body=payload, headers=self.headers)

    def parse(self, response):
        json = response.json()
        posts = json['data']['categoryTopicList']['edges']
        self.logger.debug("Current page: " + str(self.page))
        for post in posts:
            node = post['node']
            # pass pinned post
            if (node['pinned']) is True:
                continue
            item = self.getItem(node)


            if (self.has_reached_lasttime(item) == True):
                self.reach_last_date_counter += 1
                self.logger.debug("Meet an old post")
            yield item
        
        if self.reach_last_date_counter < 10 and self.page < self.page_range:
            self.page += 1
            payload = self.payload_frame[0]+str(15*(self.page-1))+self.payload_frame[1]
            yield scrapy.Request(url=self.url, callback=self.parse, method="POST", body=payload, headers=self.headers)

    def getItem(self, node):
        item = CrawlerLeetcodeItem()
        # title
        item['title'] = node['title']
        # author
        if node['post']['author'] is not None:
            item['author'] = node['post']['author']['username']
        # create time
        item['create_date'] = time.strftime("%Y-%m-%d",time.localtime(node['post']['creationDate']))
        # last reply time
        # if node['lastComment'] is not None:
        #     item['last_reply_date'] = time.strftime("%Y-%m-%d",time.localtime(node['lastComment']['post']['creationDate']))
        # tags
        if node['tags'] != []:
            item['tags'] = []
            for tag in node['tags']:
                item['tags'].append(tag['name'])
            item['tags'].sort()
        
        # company
        # 1. find from title
        # 2. find from tag
        li = node['title'].split()
        for com in li:
            com = com.capitalize()
            if com in self.companies:
                item['company'] = com
                break
        if 'company' not in item:
            for tag in node['tags']:
                for com in tag['name'].split():
                    if com in self.companies:
                        item['company'] = com
                        break
        return item
        
    def has_reached_lasttime(self, item):
        coll = 'interview_questions'
        post = ItemAdapter(item).asdict()
        collection = self.db[coll]
        return collection.count_documents(post) != 0
        
        
