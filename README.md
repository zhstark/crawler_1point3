该项目包含两个独立的子项目：

- crawler_1point3: 统计一亩三分地帖子数据，可以查看近期哪些公司热度比较高
- crawler_leetcode(WIP): 统计 LeetCode 面经数据。

## 简介

目前支持：
1. 一亩三分地“[求职（非面经）](https://www.1point3acres.com/bbs/forum-28-1.html)”，可统计公司话题热度 
2. 一亩三分地“[面经](https://www.1point3acres.com/bbs/forum-145-1.html)” ，可统计公司招聘热度
3. LeetCode [Interview Questions](https://leetcode.com/discuss/interview-question?currentPage=1&orderBy=newest_to_oldest&query=)

爬虫只将帖子数据写入数据，可参考 crawler_web 进行网页展示，若只想本地看统计数据的话可以在 [pipeline.py](crawler_1point3/pipelines.py) 中取消 `# self.create_forms_by_db()` 注释，在 `company_list` 中添加想要看到的公司名，其会在本地创建一个 markdown 文件，统计数据将以 markdown 表格的形式展示。

由于一亩三分地的帖子是按照回复时间排序的，而 LeetCode 可以按照发帖顺序排序，所以两个爬虫在 判断是否达到上次爬过的内容 上有所不同。

一亩三分地每个帖子里面会有公司的 tag，所以提取公司比较容易，而 LeetCode 格式没那么严格，只能在标题和 tag 里提取字段，判断是否是公司名，公司名单列表存在单独的文件 [company_list.py](crawler_leetcode/crawler_leetcode/company_list.py)里面方便修改。

## Prerequisite

安装 python 包 (*python3*)： 
- scrapy
- pymongo

安装、启动 MongoDB

## 使用说明

在 [setting.py](crawler_1point3/crawler_1point3/settings.py) 中设置数据库相关配置及最多爬多少页。（这里不用担心设置页数范围太大而导致每次都耗时很久，如果爬虫发现自己爬到了上次已经爬过的帖子时自动停止）

运行：

```cmd
$ sh run.sh
```

### 运行单个爬虫

如果只想运行某一个爬虫，则进入其目录，运行 `scrapy crawl <spider-name>`

eg.

```
$ cd crawler_1point3
$ scrapy crawl Spider1point3 
```

如要存储 log, 添加参数：

```
 --logfile ./spider.log
```

所有数据会写入数据库。可用 crawler_web 网页展示，若只想本地看统计数据的话可以在 [pipeline.py](crawler_1point3/crawler_1point3/pipelines.py) 中取消 `# self.create_forms_by_db()` 注释，在 `company_list` 中添加想要看到的公司名，其会在本地创建一个 markdown 文件，统计数据将以 markdown 表格的形式展示。

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

### 一亩三分地爬虫

<!-- 考虑再三还是先选择 MongoDB。因为就应用来讲不会有太多写入和并发现象，爬虫写入一次之后主要还是以读取为主，故不需要考虑关系型数据库的 ACID 特性。为了方便使用以及日后方便的可扩展性，选择 MongoDB。 -->
每次调用爬虫会操作三个 collection：

#### 1. jobs

该 collection 存储所有关于“求职”栏的帖子

Document example:

```
{'author': 'jgjgbobo',
 'company': 'Amazon',
 'create_date': '2020-07-17',
 'last_reply_date': '2020-07-17',
 'post': 'jobs',
 'title': '请问下亚麻社招流程'}
```

| Key | 备注 |
| --- | ---- |
| title | 帖子标题 |
| author | 作者 |
| create_date | 帖子创建日期 |
| last_reply_date | 最新回复日期 |
| company | 公司名 |
| post | 'jobs' |

#### 2. interviews

该 collection 存储所有关于“面经”栏的帖子

Document example:

```
{'apply_method': '猎头',
 'author': 'wx6807',
 'company': 'Kuaishou',
 'create_date': '2020-07-20',
 'interview_type': '技术电面\xa0',
 'last_reply_date': '2020-07-20',
 'position': '全职',
 'post': 'interviews',
 'title': '快手电面挂经'}
 ```

| Key | 备注 |
| --- | ---- |
| apply_method | 申请方式（猎头/内推等） |
| inerview_type | 面试类型（店面/onsite 等） |
| position | 全职/实习 |
| post | 'interviews' |

#### 3. spider_work_date

该 collection 用于记录 spider 调用过的日期

### LeetCode 面经爬虫

只有一个 collection -- `interview_questions`，记录每个帖子信息