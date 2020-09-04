FROM scrapinghub/scrapinghub-stack-scrapy:1.8-py3

WORKDIR /app

ADD ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ /app
CMD ["scrapy", "crawl", "app_store"]