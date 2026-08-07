

This project contains two independent subprojects:

- crawler_1point3: Crawls post data from 1point3acres, allowing you to see which companies are trending recently.
- crawler_leetcode (WIP): Crawls LeetCode interview experience data.

## Introduction

Currently supported:
1. 1point3acres "[Job Hunt (Non-Interview)](https://www.1point3acres.com/bbs/forum-28-1.html)", allows tracking company topic popularity.
2. 1point3acres "[Interview Experiences](https://www.1point3acres.com/bbs/forum-145-1.html)", allows tracking company hiring popularity.
3. LeetCode [Interview Questions](https://leetcode.com/discuss/interview-question?currentPage=1&orderBy=newest_to_oldest&query=)

The crawler only writes post data to the database. You can refer to [crawler_web](https://github.com/zhstark/crawler_1point3_web) for web display. If you only want to view the statistics locally, uncomment `# self.create_forms_by_db()` in [pipeline.py](crawler_1point3/pipelines.py), add the company names you want to see to `company_list`, and it will create a local markdown file where the statistics will be displayed in a markdown table.

Since 1point3acres posts are sorted by reply time, while LeetCode posts can be sorted by creation time, the two crawlers differ in how they determine if they have reached previously crawled content.

1point3acres posts usually contain company tags, making company extraction straightforward. LeetCode's format is less strict, so we can only extract fields from titles and tags to determine if they are company names. The list of companies is stored in a separate file [company_list.py](crawler_leetcode/crawler_leetcode/company_list.py) for easy modification.

## Prerequisite

Install Python packages (*python3*): 
- scrapy
- pymongo

Install and start MongoDB.

## Usage

Set database-related configurations and the maximum number of pages to crawl in [setting.py](crawler_1point3/crawler_1point3/settings.py). (Don't worry about setting a large page range causing long run times every time; the crawler will automatically stop when it detects it has reached previously crawled posts.)

Run:

```cmd
$ sh run.sh
```

### Running a Single Crawler

If you only want to run a specific crawler, navigate to its directory and run `scrapy crawl <spider-name>`.

e.g.

```
$ cd crawler_1point3
$ scrapy crawl Spider1point3 
```

To save logs, add the following parameter:

```
 --logfile ./spider.log
```

All data will be written to the database. It can be displayed via web using [crawler_web](https://github.com/zhstark/crawler_1point3_web). If you only want to view the statistics locally, uncomment `# self.create_forms_by_db()` in [pipeline.py](crawler_1point3/crawler_1point3/pipelines.py), add the company names you want to see to `company_list`, and it will create a local markdown file where the statistics will be displayed in a markdown table.

## Workflow Overview:

```
        get         Not Crawled           Job Post   
spider -----> post --------->  item -------> insert to collection "jobs"
                |                |
                | Crawled            | Interview Post
                |                | 
                V                V
               pass         insert collection "interviews"
```

## Database

### 1point3acres Crawler

<!-- 考虑再三还是先选择 MongoDB。因为就应用来讲不会有太多写入和并发现象，爬虫写入一次之后主要还是以读取为主，故不需要考虑关系型数据库的 ACID 特性。为了方便使用以及日后方便的可扩展性，选择 MongoDB。 -->
Each crawler invocation operates on three collections:

#### 1. jobs

This collection stores all posts from the "Job Hunt" section.

Document example:

```
{'author': 'jgjgbobo',
 'company': 'Amazon',
 'create_date': '2020-07-17',
 'last_reply_date': '2020-07-17',
 'post': 'jobs',
 'title': '请问下亚麻社招流程'}
```

| Key | Description |
| --- | ----------- |
| title | Post title |
| author | Author |
| create_date | Post creation date |
| last_reply_date | Last reply date |
| company | Company name |
| post | 'jobs' |

#### 2. interviews

This collection stores all posts from the "Interview Experience" section.

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

| Key | Description |
| --- | ----------- |
| apply_method | Application method (headhunter/referral, etc.) |
| inerview_type | Interview type (phone/onsite, etc.) |
| position | Full-time/Internship |
| post | 'interviews' |

#### 3. spider_work_date

This collection is used to record the dates the spider has been run.

### LeetCode Interview Crawler

Has only one collection -- `interview_questions`, recording information for each post.
