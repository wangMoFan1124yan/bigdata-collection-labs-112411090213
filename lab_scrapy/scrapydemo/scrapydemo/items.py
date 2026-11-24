# -*- coding: utf-8 -*-
# Define here the models for your scraped items
#
# See documentation: https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapydemoItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    content = scrapy.Field()  # 名言内容
    author = scrapy.Field()  # 作者
    tags = scrapy.Field()  # 标签（列表）
