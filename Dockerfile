FROM python:3.7

WORKDIR /code

COPY requirements.txt ./

COPY crawler_1point3 crawler_1point3/

COPY crawler_leetcode crawler_leetcode/

RUN pip install --no-cache-dir -r requirements.txt

COPY run.sh ./
COPY run.py ./