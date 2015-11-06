# -*- coding: utf-8 -*-
from scrapy.item import Item, Field


class PersonItem(Item):
    imdbId = Field()
    url = Field()
    types = Field()
    ranking = Field()
    name = Field()
    birthDate = Field()
    birthName = Field()
    birthPlace = Field()
    quotes = Field()
