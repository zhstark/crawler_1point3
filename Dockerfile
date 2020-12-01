FROM python:3.7

WORKDIR /code

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY crawler_1point3/ ./crawler_1point3

COPY crawler_leetcode/ ./crawler_leetcode

COPY run.sh ./

CMD sh run.sh