# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient


class ParseSocialMediaPipeline:
    def __init__(self):
        super().__init__()
        client = MongoClient('127.0.0.1', 27017)
        self.mongo_base = client.groups

    def process_item(self, item, spider):
        if item['type'] == 'group':
            collections_item = self.mongo_base['vk_parse_groups']
            for i in item['data']:
                collections_item.insert_one(i)
        elif item['type'] == 'wall':
            collections_item = self.mongo_base['vk_parse_wall']
            collections_item.insert_one(dict(item))
        else:
            collections_item = self.mongo_base['other']
        return item
