#!/usr/bin/python3
# -*- coding: utf-8 -*-


import os
import logging
from time import time, sleep
import pymongo
import settings

mongo_url=settings.MONGO_URL

check_timeout = 30
check_interval = 1
interval_unit = "second" if check_interval == 1 else "seconds"


start_time = time()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def pg_isready():
    while time() - start_time < check_timeout:
        try:
            client = pymongo.MongoClient(host=mongo_url, serverSelectionTimeoutMS = 500)
            client.server_info()
            logger.info("mongo is ready! ✨ 💅")
            client.close()
            return True
        except:
            logger.info(
                f"Mongo isn't ready. Waiting for {check_interval} {interval_unit}..."
            )
            sleep(check_interval)

    logger.error(f"We could not connect to Mongo within {check_timeout} seconds.")
    return False


pg_isready()
