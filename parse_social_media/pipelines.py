# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
from scrapy.pipelines.images import ImagesPipeline, FilesPipeline
import scrapy


class ParseSocialMediaPipeline:
    def __init__(self):
        super().__init__()
        client = MongoClient('127.0.0.1', 27017)
        self.mongo_base = client.groups

    def process_item(self, item, spider):
        if item['type'] == 'group':
            collections_item = self.mongo_base['vk_parse_groups']
            for i in item['data']:
                if not collections_item.find_one({'id': i['id']}):
                    collections_item.insert_one(i)
        elif item['type'] in ('wall', 'update'):
            collections_item = self.mongo_base['vk_parse_wall']
            if not collections_item.find_one({'hash_post': item['hash_post']}):
                collections_item.insert_one(dict(item))
        return item


class ParseSocialMediaGroupsPipelines:
    def process_item(self, item, spider):
        return item


class ParseSocialMediaPostsPipelines:
    def process_item(self, item, spider):
        return item


class ParseSocialMediaPhotosPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        try:
            if item['type'] == 'wall' and item['content']:
                for file in item['content']:
                    cat = (
                        "posted_photo", "graffiti", "video", "photo", "album", "doc", "link", "poll",
                        "market", "market_album", "photos_list", "app", "sticker", "pretty_cards"
                    )
                    # получаем контент с типом photo
                    if file["type"] in cat:
                        url_photo = ''
                        try:
                            if file["type"] == "posted_photo" and "photo_604" in file["posted_photo"]:
                                # получаем url самой большой фото
                                url_photo = file["posted_photo"]['photo_604']
                            elif file["type"] == "graffiti" and "photo_586" in file["graffiti"]:
                                url_photo = file["graffiti"]["photo_586"]
                            elif file["type"] == "video" and "image" in file["video"]:
                                # получаем url обложки видео
                                big_photo = min(file['video']['image'], key=lambda x: x['width'])
                                url_photo = big_photo['url']
                            elif file["type"] == "photo" and "sizes" in file["photo"]:
                                # получаем url самой большой фото
                                big_photo = min(file['photo']['sizes'], key=lambda x: x['width'])
                                url_photo = big_photo['url']
                            elif file["type"] == "album" and "thumb" in file["album"]:
                                # получаем url самой большой фото обложки
                                big_photo = min(file['album']['thumb']['sizes'], key=lambda x: x['width'])
                                url_photo = big_photo['url']
                            if file["type"] == "doc" and "preview" in file["doc"]:
                                big_photo = min(file['doc']['preview']['photo']['sizes'], key=lambda x: x['width'])
                                url_photo = big_photo['url']
                            elif file["type"] == "link" and "photo" in file["link"]:
                                big_photo = min(file['link']['photo']['sizes'], key=lambda x: x['width'])
                                url_photo = big_photo['url']
                            elif file["type"] == "app":
                                # file['app']['photo_604'] or file['app']['photo_130']
                                pass
                            elif file["type"] == "poll" and "photo" in file['poll']:
                                if "background" in file['poll']:
                                    pass
                                big_photo = min(file['poll']['photo']['images'], key=lambda x: x['width'])
                                url_photo = big_photo['url']
                            elif file["type"] == "photos_list":
                                pass
                            elif file["type"] == "market" and 'thumb_photo' in file['market']:
                                url_photo = file['market']['thumb_photo']
                                # file['market']['thumb-photo'] or file['market']['photos']
                            elif file["type"] == "market_album" and "photo" in file['market_album']:
                                big_photo = min(file['market_album']['photo']['sizes'], key=lambda x: x['width'])
                                url_photo = big_photo['url']
                            elif file["type"] == "sticker":
                                # file['sticker']['images'] or file['sticker']['images_with_background']
                                pass
                            elif file["type"] == "pretty_cards":
                                # file['pretty_cards']['images']
                                pass
                            yield scrapy.Request(url_photo)
                        except Exception as e:
                            print(e)
        except KeyError as e:
            print(e)

    def item_completed(self, results, item, info):
        if results:
            item['photo'] = [itm[1] for itm in results if itm[0]]
        return item


class ParseSocialMediaVideosPipelines(FilesPipeline):
    def get_media_requests(self, item, info):
        if item['type'] == 'wall' and item["content"]:
            for file in item['content']:
                pass

    def item_completed(self, results, item, info):
        if results:
            item['video'] = [itm[1] for itm in results if itm[0]]
        return item
