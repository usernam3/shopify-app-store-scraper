# -*- coding: utf-8 -*-
from scrapy import Request
import re
import uuid
import hashlib
from .lastmod_spider import LastmodSpider
from ..items import App, KeyBenefit, PricingPlan, PricingPlanFeature, Category, AppCategory, AppReview
from bs4 import BeautifulSoup
import pandas as pd

from ..pipelines import WriteToCSV


class AppStoreSpider(LastmodSpider):
    BASE_DOMAIN = "apps.shopify.com"

    name = 'app_store'

    allowed_domains = ['apps.shopify.com']
    sitemap_urls = ['https://apps.shopify.com/sitemap.xml']
    sitemap_rules = [
        (re.compile(LastmodSpider.APP_URL_REGEX), 'parse')
    ]

    # Apps that were already scraped
    processed_apps = {}
    # Reviews that were already scraped
    processed_reviews = {}

    def start_requests(self):
        # Fetch existing apps from CSV
        apps = pd.read_csv('{}{}{}'.format('./', WriteToCSV.OUTPUT_DIR, 'apps.csv'))
        for _, app in apps.iterrows():
            self.processed_apps[app['url']] = {'url': app['url'], 'lastmod': app['lastmod'], 'id': app['id']}

        self.processed_reviews = pd.read_csv('{}{}{}'.format('./', WriteToCSV.OUTPUT_DIR, 'reviews.csv'))

        for url in self.sitemap_urls:
            yield Request(url, self._parse_sitemap)

    def parse(self, response):
        app_id = str(uuid.uuid4())
        app_url = response.url
        persisted_app = self.processed_apps.get(app_url, None)

        if persisted_app is not None:
            if persisted_app.get('lastmod') != response.meta['lastmod']:
                self.logger.info('App\'s page got updated since %s, taking the existing id %s | URL: %s',
                                 persisted_app.get('lastmod'), persisted_app.get('id'), app_url)
                # Take id of the existing app
                app_id = persisted_app.get('id', app_id)

        response.meta['app_id'] = app_id
        self.processed_apps[app_url] = {
            'id': app_id,
            'url': app_url,
            'lastmod': response.meta['lastmod'],
        }

        self.parse_app(response)

        reviews_url = '{}{}'.format(app_url, '/reviews')
        yield Request(reviews_url, callback=self.parse_reviews, meta={'app_id': app_id, 'lastmod': response.meta['lastmod'], 'skip_if_first_scraped': True})

    @staticmethod
    def close(spider, reason):
        spider.logger.info('Spider closed: %s', spider.name)

        # Normalize categories
        spider.logger.info('Preparing unique categories...')
        categories_df = pd.read_csv('output/categories.csv')
        categories_df.drop_duplicates(subset=['id', 'title']).to_csv('output/categories.csv', index=False)
        spider.logger.info('Unique categories are there 👌')

        # Normalize apps
        spider.logger.info('Preparing unique apps...')
        apps_df = pd.read_csv('output/apps.csv')
        apps_df.drop_duplicates(subset=['id'], keep='last').to_csv('output/apps.csv', index=False)
        spider.logger.info('Unique apps are there 💎')

        # Normalize reviews
        spider.logger.info('Preparing unique reviews...')
        apps_df = pd.read_csv('output/reviews.csv')
        apps_df.drop_duplicates(subset=['app_id', 'author', 'posted_at'], keep='last').to_csv('output/reviews.csv',
                                                                                              index=False)
        spider.logger.info('Unique reviews are there 🔥')

        return super().close(spider, reason)

    def parse_app(self, response):
        """ Contract specifies the expected output

        @url https://apps.shopify.com/calendify
        @meta {"app_id": "9f0b03f2-e3b5-4c29-bc0e-0393852bcf43", "lastmod": "2022-03-17"}
        @output_matches parse_app/calendify.json
        """

        app_id = response.meta['app_id']

        url = response.request.url
        title = response.css('#adp-hero h1 ::text').extract_first(default='').strip()
        developer = response.css('#adp-hero a[href^=\/partners]::text').extract_first().strip()
        developer_link = 'https://{}{}'.format(self.BASE_DOMAIN, response.css('#adp-hero a[href^=\/partners]::attr(href)').extract_first().strip())
        icon = response.css('#adp-hero img::attr(src)').extract_first()
        rating = response.css('#adp-hero dd > span.tw-text-fg-secondary ::text').extract_first()
        reviews_count_raw = response.css('#reviews-link::text').extract_first(default='0 Reviews')
        reviews_count = int(''.join(re.findall(r'\d+', reviews_count_raw)))
        description_raw = response.css('#app-details').extract_first()
        description = ' '.join(response.css('#app-details ::text').extract()).strip()
        tagline = None
        pricing_hint = response.css('#adp-hero > div > div.tw-grow.tw-flex.tw-flex-col.tw-gap-xl > dl > div:nth-child(1) > dd > div.tw-hidden.sm\:tw-block.tw-text-pretty ::text').extract_first().strip()

        for benefit in response.css('#app-details>ul>li'):
            yield KeyBenefit(app_id=app_id,
                             title=None, # Backward-compatibility with format 1.0
                             description=benefit.css('::text').extract_first().strip())

        for pricing_plan in response.css('.app-details-pricing-plan-card'):
            pricing_plan_id = str(uuid.uuid4())
            yield PricingPlan(id=pricing_plan_id,
                              app_id=app_id,
                              title=pricing_plan.css('[data-test-id="name"] ::text').extract_first(default='').strip(),
                              price=pricing_plan.css('.app-details-pricing-format-group::attr(aria-label)').extract_first().strip())

            for feature in pricing_plan.css('ul[data-test-id="features"] li'):
                yield PricingPlanFeature(pricing_plan_id=pricing_plan_id, app_id=app_id,
                                         feature=' '.join(feature.css('::text').extract()).strip())

        for category_raw in response.css('#adp-details-section > div.tw-flex.tw-flex-col.tw-gap-lg.lg\:tw-gap-2xl > div:nth-child(2) > div > span a::text').extract():
            category = category_raw.strip()
            category_id = hashlib.md5(category.lower().encode()).hexdigest()

            yield Category(id=category_id, title=category)
            yield AppCategory(app_id=app_id, category_id=category_id)

        yield App(
            id=app_id,
            url=url,
            title=title,
            developer=developer,
            developer_link=developer_link,
            icon=icon,
            rating=rating,
            reviews_count=int(next(iter(re.findall(r'\d+', str(reviews_count))), '0')),
            description_raw=description_raw,
            description=description,
            tagline=tagline,
            pricing_hint=pricing_hint,
            lastmod=response.meta['lastmod']
        )

    def parse_reviews(self, response):
        app_id = response.meta['app_id']
        skip_if_first_scraped = response.meta.get('skip_if_first_scraped', False)

        for idx, review in enumerate(response.css('[data-merchant-review]')):
            author = review.css('div.tw-text-heading-xs.tw-text-fg-primary.tw-overflow-hidden.tw-text-ellipsis.tw-whitespace-nowrap ::text').extract_first(default='').strip()
            rating = review.css('[aria-label]::attr(aria-label)').extract_first(default='').strip().split()[0]
            posted_at = review.css('div.tw-flex.tw-items-center.tw-justify-between.tw-mb-md > div.tw-text-body-xs.tw-text-fg-tertiary ::text').extract_first(default='').strip()
            raw_body = BeautifulSoup(review.css('[data-truncate-review],[data-truncate-content-copy]').extract_first(), features='lxml')
            for button in raw_body.find_all('button'):
                button.decompose()
            body = raw_body.get_text().strip()
            helpful_count = review.css('.review-helpfulness .review-helpfulness__helpful-count ::text').extract_first()
            developer_reply = BeautifulSoup(review.css('[data-reply-id]').extract_first(default=''), features='lxml').get_text().strip()
            developer_reply_posted_at = review.css('[id^=review-reply-] .tw-text-fg-tertiary::text').extract_first(default='').strip().split('\n')[-1].strip()

            # Stop scraping if last review was already scraped (means that there are no new reviews for this app)
            if skip_if_first_scraped and idx == 0:
                existing_review = self.processed_reviews.loc[
                    (self.processed_reviews['app_id'] == app_id) &
                    (self.processed_reviews['author'] == author) &
                    (self.processed_reviews['rating'] == int(rating)) &
                    (self.processed_reviews['posted_at'] == posted_at) &
                    (self.processed_reviews['body'] == body)
                    ]

                if not existing_review.empty:
                    self.logger.info("The last review of app was already scrapped, skipping the rest | App id : %s",
                                     app_id)
                    return None

            yield AppReview(
                app_id=app_id,
                author=author,
                rating=rating,
                posted_at=posted_at,
                body=body,
                helpful_count=helpful_count,
                developer_reply=developer_reply,
                developer_reply_posted_at=developer_reply_posted_at
            )

        next_page_url = response.css('[rel="next"]::attr(href)').extract_first()
        if next_page_url:
            yield Request(next_page_url, callback=self.parse_reviews,
                          meta={'app_id': response.meta['app_id']})
