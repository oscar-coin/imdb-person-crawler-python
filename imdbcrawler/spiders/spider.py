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
    db = None
    collection_name = None

    def parse(self,response):
        for idx, sel in enumerate(response.xpath("//*[@class='results']/tr")):
            if idx == 0:
                continue

            raw_url = self.get_xpath("*[@class='name']/a/@href", sel, 0)
            imdb_id = self.resolve_id(raw_url, '/name/')

            # Db lookup
            if self.db[self.collection_name].find({'imdbId': imdb_id}).limit(1).count() > 0:
                continue

            item = PersonItem()
            self.set_item(item, 'imdbId', imdb_id)
            self.set_item(item, 'url', response.urljoin(raw_url))

            yield scrapy.Request(response.urljoin(item['url']), meta={'item': item}, callback=self.parse_person, priority=1)

        # get the next page
        next_page = response.xpath("//*[@class='pagination']/a/@href").extract()[-1]
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse)

    def parse_person(self, response):
        item = response.meta['item']

        self.set_item(item, "ranking", self.get_xpath("//*[@id='meterRank']/text()", response, 0))
        self.set_item(item, "name", self.get_xpath("//*[@itemprop='name']/text()", response, 0))

        self.set_item(item, "birthDate", self.get_xpath("//*[@id='name-born-info']/time/@datetime", response, 0))

        if len(response.xpath("//*[@id='name-born-info']/a/text()").extract()) == 1:
            self.set_item(item, "birthPlace", self.get_xpath("//*[@id='name-born-info']/a[1]/text()", response, 0))
        else:
            self.set_item(item, "birthName", self.get_xpath("//*[@id='name-born-info']/a[1]/text()", response, 0))
            self.set_item(item, "birthPlace", self.get_xpath("//*[@id='name-born-info']/a[2]/text()", response, 0))

        self.set_item(item, "types", self.get_xpath("//*[@id='name-job-categories']/a/span/text()", response, -1))

        return scrapy.Request(item["url"] + self.biography_endpoint, meta={'item': item}, callback=self.parse_biography, priority=2)

    def parse_biography(self, response):
        item = response.meta['item']
        start_index = 0
        quotes = []
        for idx, sel in enumerate(response.xpath("//*[@id='bio_content']/*[not(self::script)]")):
            if sel.xpath("text()") and "Personal Quotes" in sel.xpath("text()").extract()[0]:
                start_index = 1
            elif start_index != 0 and not sel.xpath("text()"):
                break
            elif start_index != 0:
                quote = re.sub("<[^>]*>", "", "".join(sel.xpath("node()").extract()).strip())
                if quote:
                    quotes.append(quote)
        self.set_item(item, "quotes", quotes)
        return item

    @staticmethod
    def resolve_id(url, sub):
        return re.sub('/.*?.*', '', re.sub(sub, '', url))

    @staticmethod
    def set_item(item, key, prop):
        if not prop or (hasattr(prop, "__len__") and not len(prop) > 0):
            return
        item[key] = prop

    @staticmethod
    def get_xpath(path, response, index):
        parsed = response.xpath(path)
        if parsed:
            striped = [x.strip() for x in parsed.extract()]
            if index < 0 or index > len(striped)-1:
                return striped
            return striped[index]
        return None
