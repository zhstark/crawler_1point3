统计一亩三分地帖子数据，可以查看近期哪些公司热度比较高

## Prerequisite

安装 python 包： 
- scrapy
- pymongo

安装、启动 MongoDB

## 使用说明

在 [setting.py](crawler_1point3/settings.py) 中设置数据库相关配置及最多爬多少页。（这里不用担心设置页数范围太大，如果爬虫发现自己爬到了上次已经爬过的帖子时自动停止）

运行：

```
$ scrapy crawl Spider1point3 --logfile ./spider.log
```

所有数据会写入数据库。可用 crawler_1point3_web 网页展示，若只想本地看统计数据的话可以在 [pipeline.py](crawler_1point3/pipelines.py) 中取消 `# self.create_forms_by_db()` 注释，在 `company_list` 中添加想要看到的公司名，其会在本地创建一个 markdown 文件，统计数据将以 markdown 表格的形式展示。

## 流程简介：

```
        get         没有爬过           求职贴   
spider -----> post --------->  item -------> insert to collection "jobs"
                |                |
                | 爬过            | 面经贴
                |                | 
                V                V
               pass         insert collection "interviews"
```

## 数据库

<!-- 考虑再三还是先选择 MongoDB。因为就应用来讲不会有太多写入和并发现象，爬虫写入一次之后主要还是以读取为主，故不需要考虑关系型数据库的 ACID 特性。为了方便使用以及日后方便的可扩展性，选择 MongoDB。 -->