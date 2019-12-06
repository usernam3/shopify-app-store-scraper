FROM scrapinghub/scrapinghub-stack-scrapy:1.8-py3

COPY ./ /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt
CMD ["scrapy", "crawl", "app_store"]