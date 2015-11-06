# -*- coding: utf-8 -*-

from scrapy.item import Item, Field

class PersonItem(Item):
    imdbId = Field()
    url = Field()
    types = Field()
    starMeter = Field()
    name = Field()
    birthDate = Field()
    bornName = Field()
    bornPlace = Field()
    quotes = Field()
