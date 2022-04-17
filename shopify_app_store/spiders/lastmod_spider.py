# -*- coding: utf-8 -*-
import scrapy
from abc import ABCMeta
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots


class LastmodSpider(scrapy.spiders.SitemapSpider, metaclass=ABCMeta):

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
                            yield scrapy.Request(entry['loc'], callback=c, meta={'lastmod': entry['lastmod']})
                            break
