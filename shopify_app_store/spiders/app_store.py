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
    REVIEWS_REGEX = r"(.*?)/reviews$"
    BASE_DOMAIN = "apps.shopify.com"

    name = 'app_store'

    allowed_domains = ['apps.shopify.com']
    sitemap_urls = ['https://apps.shopify.com/sitemap.xml']
    sitemap_rules = [
        (re.compile(REVIEWS_REGEX), 'parse')
    ]

    # Apps that were already scraped
    processed_apps = {}

    def start_requests(self):
        # Fetch existing apps from CSV
        apps = pd.read_csv('{}{}{}'.format('./', WriteToCSV.OUTPUT_DIR, 'apps.csv'))
        for _, app in apps.iterrows():
            self.processed_apps[app['url']] = {'url': app['url'], 'lastmod': app['lastmod'], 'id': app['id']}

        for url in self.sitemap_urls:
            yield Request(url, self._parse_sitemap)

    def parse(self, response):
        app_id = str(uuid.uuid4())
        app_url = re.compile(self.REVIEWS_REGEX).search(response.url).group(1)
        persisted_app = self.processed_apps.get(app_url, None)

        if persisted_app is not None:
            if persisted_app.get('lastmod') == response.meta['lastmod']:
                self.logger.info('Skipping app as it hasn\'t changed since %s | URL: %s', persisted_app.get('lastmod'),
                                 app_url)
                # Skip apps which were scraped and haven't changed since they were added to the list
                yield None
            else:
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

        yield Request(app_url, callback=self.parse_app, meta={'app_id': app_id, 'lastmod': response.meta['lastmod']})
        # @TODO Make sure that reviews are also lastmod aware
        for review in self.parse_reviews(response):
            yield review

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

        return super().close(spider, reason)

    def parse_app(self, response):
        """ Contract specifies the expected output

        @url https://apps.shopify.com/calendify
        @meta {"app_id": "9f0b03f2-e3b5-4c29-bc0e-0393852bcf43", "lastmod": "2022-03-17"}
        @output_matches parse_app/calendify.json
        """

        app_id = response.meta['app_id']

        url = response.request.url
        title = response.css('.vc-app-listing-hero__heading ::text').extract_first(default='').strip()
        developer = response.css('.vc-app-listing-hero__by-line a::text').extract_first()
        developer_link = response.css('.vc-app-listing-hero__by-line a::attr(href)').extract_first()
        icon = response.css('.vc-app-listing-about-section__title img::attr(src)').extract_first()
        rating = response.css('.ui-star-rating__rating ::text').extract_first()
        reviews_count = response.css('.ui-review-count-summary a::text').extract_first(default='0 reviews')
        description_raw = response.css('.vc-app-listing-about-section__description').extract_first()
        description = ' '.join(response.css('.vc-app-listing-about-section__description ::text').extract()).strip()
        tagline = ' '.join(response.css('.vc-app-listing-hero__tagline ::text').extract()).strip()
        pricing_hint = response.css('.ui-app-pricing--format-detail ::text').extract_first(default='').strip()

        for benefit in response.css('.vc-app-listing-key-values__item'):
            yield KeyBenefit(app_id=app_id,
                             title=benefit.css('.vc-app-listing-key-values__item-title ::text').extract_first().strip(),
                             description=benefit.css(
                                 '.vc-app-listing-key-values__item-description ::text').extract_first().strip())

        for pricing_plan in response.css('.ui-card.pricing-plan-card'):
            pricing_plan_id = str(uuid.uuid4())
            yield PricingPlan(id=pricing_plan_id,
                              app_id=app_id,
                              title=pricing_plan.css('.pricing-plan-card__title-kicker ::text').extract_first(
                                  default='').strip(),
                              price=pricing_plan.css('h3 ::text').extract_first().strip())

            for feature in pricing_plan.css('ul li.bullet'):
                yield PricingPlanFeature(pricing_plan_id=pricing_plan_id, app_id=app_id,
                                         feature=' '.join(feature.css('::text').extract()).strip())

        for category in response.css('.vc-app-listing-hero__taxonomy-links a::text').extract():
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

        for review in response.css('div.review-listing'):
            author = review.css('.review-listing-header>h3 ::text').extract_first(default='').strip()
            rating = review.css(
                '.review-metadata>div:nth-child(1) .ui-star-rating::attr(data-rating)').extract_first(
                default='').strip()
            posted_at = review.css(
                '.review-metadata>div:nth-child(2) .review-metadata__item-value ::text').extract_first(
                default='').strip()
            body = BeautifulSoup(review.css('.review-content div').extract_first(), features='lxml').get_text().strip()
            helpful_count = review.css('.review-helpfulness .review-helpfulness__helpful-count ::text').extract_first()
            developer_reply = BeautifulSoup(
                review.css('.review-reply .review-content div').extract_first(default=''),
                features='lxml').get_text().strip()
            developer_reply_posted_at = review.css(
                '.review-reply div.review-reply__header-item ::text').extract_first(default='').strip()

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

        next_page_path = response.css('a.search-pagination__next-page-text::attr(href)').extract_first()
        if next_page_path:
            yield Request('https://{}{}'.format(self.BASE_DOMAIN, next_page_path), callback=self.parse_reviews,
                          meta={'app_id': response.meta['app_id']})
