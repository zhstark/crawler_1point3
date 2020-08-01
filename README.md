统计一亩三分地帖子数据

## Prerequisite

安装 python 包： 
- scrapy
- pymongo

安装、启动 MongoDB

## 使用说明

运行：

```
$ scrapy crawl Spider1point3 --logfile ./spider.log
```

## 数据库

考虑再三还是先选择 MongoDB。因为就应用来讲不会有太多写入和并发现象，爬虫写入一次之后主要还是以读取为主，故不需要考虑关系型数据库的 ACID 特性。为了方便使用以及日后方便的可扩展性，选择 MongoDB。