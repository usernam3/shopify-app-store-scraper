# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import csv
from .items import App, KeyBenefit, PricingPlan, PricingPlanFeature, Category, AppCategory, AppReview


class ShopifyAppStorePipeline(object):
    def process_item(self, item, spider):
        return item


class WriteToCSV(object):
    OUTPUT_DIR = './output/'

    def open_spider(self, spider):
        self.write_file_headers()

    def process_item(self, item, spider):
        if isinstance(item, App):
            self.store_app(item)
            return None
        if isinstance(item, PricingPlan):
            self.store_pricing_plan(item)
            return None
        if isinstance(item, PricingPlanFeature):
            self.store_pricing_plan_feature(item)
            return None
        if isinstance(item, Category):
            self.store_category(item)
            return None
        if isinstance(item, AppCategory):
            self.store_app_category(item)
            return None
        if isinstance(item, KeyBenefit):
            self.store_key_benefit(item)
            return None
        if isinstance(item, AppReview):
            self.store_app_review(item)
            return None

        return item

    def write_file_headers(self):
        self.write_header('apps.csv',
                          ['id', 'url', 'title', 'developer', 'developer_link', 'icon', 'rating', 'reviews_count',
                           'description_raw', 'description', 'tagline', 'pricing_hint', 'lastmod'])
        self.write_header('reviews.csv',
                          ['app_id', 'author', 'rating', 'posted_at', 'body', 'helpful_count', 'developer_reply',
                           'developer_reply_posted_at'])
        self.write_header('apps_categories.csv', ['app_id', 'category_id'])
        self.write_header('categories.csv', ['id', 'title'])
        self.write_header('pricing_plans.csv', ['id', 'app_id', 'title', 'price'])
        self.write_header('pricing_plan_features.csv', ['app_id', 'pricing_plan_id', 'feature'])
        self.write_header('key_benefits.csv', ['app_id', 'title', 'description'])
        return

    def store_app(self, app):
        self.write_to_out('apps.csv', app)
        return app

    def store_pricing_plan(self, pricing_plan):
        self.write_to_out('pricing_plans.csv', pricing_plan)
        return pricing_plan

    def store_pricing_plan_feature(self, pricing_plan_feature):
        self.write_to_out('pricing_plan_features.csv', pricing_plan_feature)
        return pricing_plan_feature

    def store_category(self, category):
        self.write_to_out('categories.csv', category)
        return category

    def store_app_category(self, app_category):
        self.write_to_out('apps_categories.csv', app_category)
        return app_category

    def store_key_benefit(self, key_benefit):
        self.write_to_out('key_benefits.csv', key_benefit)
        return key_benefit

    def store_app_review(self, app_review):
        self.write_to_out('reviews.csv', app_review)
        return app_review

    def write_to_out(self, file_name, row):
        with open('{}{}'.format(self.OUTPUT_DIR, file_name), 'a', encoding='utf-8') as out:
            csv_out = csv.writer(out)
            csv_out.writerow(dict(row).values())

    def write_header(self, file_name, row):
        with open('{}{}'.format(self.OUTPUT_DIR, file_name), 'a', encoding='utf-8') as out:
            csv_out = csv.writer(out)
            csv_out.writerow(row)
