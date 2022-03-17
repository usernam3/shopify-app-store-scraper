# -*- coding: utf-8 -*-
import scrapy
from abc import ABCMeta
from scrapy.utils.sitemap import Sitemap
from urllib.parse import urljoin


class LastmodSpider(scrapy.spiders.SitemapSpider, metaclass=ABCMeta):

    def _parse_sitemap(self, response):
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


def sitemap_urls_from_robots(robots_text, base_url=None):
    """Return an iterator over all sitemap urls contained in the given
    robots.txt file
    """
    for line in robots_text.splitlines():
        if line.lstrip().lower().startswith('sitemap:'):
            url = line.split(':', 1)[1].strip()
            yield urljoin(base_url, url)
