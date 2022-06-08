# -*- coding: utf-8 -*-
import scrapy
from abc import ABCMeta
import re
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots


class LastmodSpider(scrapy.spiders.SitemapSpider, metaclass=ABCMeta):
    REVIEWS_REGEX = r"(.*?)/reviews$"
    # Apps that were already scraped
    processed_apps = {}

    def _is_loc_same_as_processed(self, url, lastmod):
        persisted_app = self.processed_apps.get(url, None)
        return (persisted_app is not None) and (persisted_app.get('lastmod') == lastmod)

    def _parse_sitemap(self, response):
        # Implementation is duplicate of scrapy.spiders.SitemapSpider (with lastmod passed as a meta prop to callbacks)
        if response.url.endswith('/robots.txt'):
            for url in sitemap_urls_from_robots(response.text, base_url=response.url):
                yield scrapy.Request(url, callback=self._parse_sitemap)
        else:
            body = self._get_sitemap_body(response)
            if body is None:
                self.logger.warning("Ignoring invalid sitemap: %(response)s",
                                    {'response': response}, extra={'spider': self})
                return

            s = Sitemap(body)
            it = self.sitemap_filter(s)

            if s.type == 'sitemapindex':
                for entry in it:
                    if any(x.search(entry['loc']) for x in self._follow):
                        yield scrapy.Request(entry['loc'], callback=self._parse_sitemap)
            elif s.type == 'urlset':
                for entry in it:
                    for r, c in self._cbs:
                        if r.search(entry['loc']):
                            app_url = re.compile(self.REVIEWS_REGEX).search(entry['loc']).group(1)
                            if self._is_loc_same_as_processed(app_url, entry['lastmod']):
                                self.logger.info('Skipping app as it hasn\'t changed since %s | URL: %s',
                                                 entry['lastmod'],
                                                 entry['loc'])
                                # Skip apps which were scraped and haven't changed since they were added to the list
                                continue

                            yield scrapy.Request(entry['loc'], callback=c, meta={'lastmod': entry['lastmod']})
                            break
