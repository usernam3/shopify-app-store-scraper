FROM scrapinghub/scrapinghub-stack-scrapy:1.8-py3

WORKDIR /app

ADD ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ /
CMD ["scrapy", "crawl", "app_store"]