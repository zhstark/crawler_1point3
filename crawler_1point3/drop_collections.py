#!/usr/bin/python3
# -*- coding: utf-8 -*-

# 删库跑路

import pymongo
import settings

collections = ["jobs", "interviews", "spider_work_date"]

mongo_uri=settings.MONGO_URL
mongo_db=settings.MONGO_DATABASE

client = pymongo.MongoClient(mongo_uri)
db = client[mongo_db]

for i in range(len(collections)):
    collection = db[collections[i]]
    collection.drop()

client.close()

