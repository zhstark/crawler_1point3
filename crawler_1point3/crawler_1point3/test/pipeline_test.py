import scrapy
import sys
sys.path.append("../")
from pipelines import Crawler1Point3Pipeline

## test process date function

date_example=["2020-5-9", "5 天前", "昨天 06:16", "5 小时前", "前天 05:23", "5 分钟前", ""]

t=Crawler1Point3Pipeline()
for x in date_example:
    print(t.get_create_date(x))