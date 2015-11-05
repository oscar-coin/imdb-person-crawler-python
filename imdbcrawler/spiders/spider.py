# -*- coding: utf-8 -*-
import re

import scrapy
from imdbcrawler.items import PersonItem


class ImdbSpider(scrapy.Spider):
    name = "ImdbActorCrawler"
    allowed_domains = ["imdb.com"]
    url_bases = ["http://www.imdb.com/"]
    start_urls = [
        "http://www.imdb.com/search/name?birth_date=1800,2016&count=100"
    ]
    biography_endpoint = "bio?ref_=nm_dyk_qt_sm#quotes"

    def parse(self,response):
        index = 0
        for idx, sel in enumerate(response.xpath("//*[@class='results']/tr")):
            if idx == 0:
                continue

            # indexing is only working when no order is set in url
            index += 1
            rawUrl = self.getXpath("*[@class='name']/a/@href", sel)[0]
            imdbId = self.resolveId(rawUrl)

            # Db lookup
            if self.db[self.collection_name].find({'imdbId': imdbId}).limit(1).count() > 0:
                continue

            item = PersonItem()
            item['ranking'] = index
            item['imdbId'] = imdbId
            item['url'] = response.urljoin(rawUrl)

            yield scrapy.Request(response.urljoin(item['url']), meta={'item':item }, callback=self.parsePerson, priority=1)

        # get the next page
        next_page = self.getXpath("//*[@class='pagination']/a/@href", response)[-1]
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse)

    def getXpath(self, path, response):
        parsed = response.xpath(path)
        if parsed:
            extracted = parsed.extract()
            return [x.strip() for x in extracted]
        return ['']

    def resolveId(self, url):
        return re.sub('/.*?.*', '', re.sub('/name/', '', url))

    def parsePerson(self, response):
        item = response.meta['item']

        item["starMeter"] = self.getXpath("//*[@id='meterRank']/text()", response)[0]
        item["name"] = self.getXpath("//*[@itemprop='name']/text()", response)[0]

        item["birthDate"] = self.getXpath("//*[@id='name-born-info']/time/@datetime", response)[0]

        if response.xpath("//*[@id='name-born-info']/a[1]/text()") and len(response.xpath("//*[@id='name-born-info']/a/text()").extract()) == 1:
            item["bornPlace"] = self.getXpath("//*[@id='name-born-info']/a[1]/text()", response)[0]
        else:
            item["bornName"] = self.getXpath("//*[@id='name-born-info']/a[1]/text()", response)[0]
            item["bornPlace"] = self.getXpath("//*[@id='name-born-info']/a[2]/text()", response)[0]
        item["types"] = self.getXpath("//*[@id='name-job-categories']/a/span/text()", response)

        return scrapy.Request(item["url"] + self.biography_endpoint, meta={'item':item }, callback=self.parseBiography, priority=2)

    def parseBiography(self, response):
        item = response.meta['item']
        startIndex = 0
        item["quotes"] = []
        for idx, sel in enumerate(response.xpath("//*[@id='bio_content']/*")):
            if sel.xpath("text()") and "Personal Quotes" in sel.xpath("text()").extract()[0]:
                startIndex = 1
            elif startIndex != 0 and (not sel.xpath("text()") or u'if (' in sel.xpath("text()").extract()[0]):
                break
            elif startIndex != 0:
                item["quotes"].append(''.join(sel.xpath("node()").extract()).strip())
        return item