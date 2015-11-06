# -*- coding: utf-8 -*-
import re

import scrapy
from imdbcrawler.items import PersonItem


class ImdbSpider(scrapy.Spider):
    name = "ImdbPersonCrawler"
    allowed_domains = ["imdb.com"]
    url_bases = ["http://www.imdb.com/"]
    start_urls = [
        "http://www.imdb.com/search/name?birth_date=1974,2016&count=100",
        "http://www.imdb.com/search/name?birth_date=1947,1973&count=100",
        "http://www.imdb.com/search/name?birth_date=1800,1946&count=100"
    ]
    biography_endpoint = "bio?ref_=nm_dyk_qt_sm#quotes"

    def parse(self,response):
        for idx, sel in enumerate(response.xpath("//*[@class='results']/tr")):
            if idx == 0:
                continue

            rawUrl = self.getXpath("*[@class='name']/a/@href", sel, 0)
            imdbId = self.resolveId(rawUrl, '/name/')

            # Db lookup
            if self.db[self.collection_name].find({'imdbId': imdbId}).limit(1).count() > 0:
                continue

            item = PersonItem()
            self.setItem(item, 'imdbId', imdbId)
            self.setItem(item, 'url', response.urljoin(rawUrl))

            yield scrapy.Request(response.urljoin(item['url']), meta={'item':item }, callback=self.parsePerson, priority=1)

        # get the next page
        next_page = response.xpath("//*[@class='pagination']/a/@href").extract()[-1]
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse)

    def parsePerson(self, response):
        item = response.meta['item']

        self.setItem(item, "ranking", self.getXpath("//*[@id='meterRank']/text()", response, 0))
        self.setItem(item, "name", self.getXpath("//*[@itemprop='name']/text()", response, 0))

        self.setItem(item, "birthDate", self.getXpath("//*[@id='name-born-info']/time/@datetime", response, 0))

        if response.xpath("//*[@id='name-born-info']/a[1]/text()") and len(response.xpath("//*[@id='name-born-info']/a/text()").extract()) == 1:
            self.setItem(item, "bornPlace", self.getXpath("//*[@id='name-born-info']/a[1]/text()", response, 0))
        else:
            self.setItem(item, "bornName", self.getXpath("//*[@id='name-born-info']/a[1]/text()", response, 0))
            self.setItem(item, "bornPlace", self.getXpath("//*[@id='name-born-info']/a[2]/text()", response, 0))

        self.setItem(item, "types", self.getXpath("//*[@id='name-job-categories']/a/span/text()", response, -1))

        return scrapy.Request(item["url"] + self.biography_endpoint, meta={'item':item }, callback=self.parseBiography, priority=2)

    def parseBiography(self, response):
        item = response.meta['item']
        startIndex = 0
        quotes = []
        for idx, sel in enumerate(response.xpath("//*[@id='bio_content']/*")):
            if sel.xpath("text()") and "Personal Quotes" in sel.xpath("text()").extract()[0]:
                startIndex = 1
            elif startIndex != 0 and (not sel.xpath("text()") or u'if (' in sel.xpath("text()").extract()[0]):
                break
            elif startIndex != 0:
                quote = re.sub("<[^>]*>", "", "".join(sel.xpath("node()").extract()).strip())
                if quote:
                    quotes.append(quote)
        self.setItem(item, "quotes", quotes)
        return item

    def resolveId(self, url, path):
        return re.sub('/.*?.*', '', re.sub(path, '', url))

    def setItem(self, item, key, property):
        if not property or (hasattr(property, "__len__") and not len(property)>0):
            return
        item[key] = property

    def getXpath(self, path, response, index):
        parsed = response.xpath(path)
        if parsed:
            striped = [x.strip() for x in parsed.extract()]
            if index < 0 or index > len(striped)-1:
                return striped
            return striped[index]
        return None