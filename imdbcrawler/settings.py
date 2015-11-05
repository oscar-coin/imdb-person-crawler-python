# -*- coding: utf-8 -*-

BOT_NAME = 'imdbcrawler'

SPIDER_MODULES = ['imdbcrawler.spiders']
NEWSPIDER_MODULE = 'imdbcrawler.spiders'
LOG_LEVEL = 'INFO'

DOWNLOAD_DELAY = 0.1
CONCURRENT_REQUESTS = 200

DEPTH_PRIORITY = 0

MONGO_URI = 'mongodb://localhost:27017/'
MONGO_DATABASE = 'hauptseminar'

# Prevent from Filtering
DUPEFILTER_CLASS = 'scrapy.dupefilters.BaseDupeFilter'
ITEM_PIPELINES = {
    'imdbcrawler.pipelines.MongoPipeline': 0
}
