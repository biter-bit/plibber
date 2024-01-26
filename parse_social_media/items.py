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
    post_id = scrapy.Field()
    group_id = scrapy.Field()
    hash_post = scrapy.Field()
    text = scrapy.Field()
    photo = scrapy.Field()
    marked_as_ads = scrapy.Field()
    views = scrapy.Field()
    likes = scrapy.Field()
    comments = scrapy.Field()
    reposts = scrapy.Field()
    date = scrapy.Field()

