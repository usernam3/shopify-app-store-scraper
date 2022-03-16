# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ShopifyAppStoreItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class App(scrapy.Item):
    id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    developer = scrapy.Field()
    developer_link = scrapy.Field()
    icon = scrapy.Field()
    rating = scrapy.Field()
    reviews_count = scrapy.Field()
    description_raw = scrapy.Field()
    description = scrapy.Field()
    tagline = scrapy.Field()
    pricing_hint = scrapy.Field()
    lastmod = scrapy.Field()


class KeyBenefit(scrapy.Item):
    app_id = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()


class PricingPlan(scrapy.Item):
    id = scrapy.Field()
    app_id = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()


class PricingPlanFeature(scrapy.Item):
    app_id = scrapy.Field()
    pricing_plan_id = scrapy.Field()
    feature = scrapy.Field()


class Category(scrapy.Item):
    id = scrapy.Field()
    title = scrapy.Field()


class AppCategory(scrapy.Item):
    app_id = scrapy.Field()
    category_id = scrapy.Field()


class AppReview(scrapy.Item):
    app_id = scrapy.Field()
    author = scrapy.Field()
    rating = scrapy.Field()
    posted_at = scrapy.Field()
    body = scrapy.Field()
    helpful_count = scrapy.Field()
    developer_reply = scrapy.Field()
    developer_reply_posted_at = scrapy.Field()
