# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ParseSocialMediaItem(scrapy.Item):
    type = scrapy.Field()
    data = scrapy.Field()


class ParseSocialMediaItemWall(scrapy.Item):
    type = scrapy.Field()
    data = scrapy.Field()
