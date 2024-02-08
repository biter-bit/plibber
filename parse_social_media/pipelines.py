# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
from scrapy.pipelines.images import ImagesPipeline, FilesPipeline
import scrapy
from PIL import Image
from io import BytesIO


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
                    i['average_coverage'] = None
                    collections_item.insert_one(i)
        elif item['type'] == 'update_group':
            # обновляем имя, кол-во подписчиков, аватарка группы
            collections_item = self.mongo_base['vk_parse_groups']
            filter_group = {"id": item['data']['id']}
            update_data = {
                "$set": {
                    "members_count": item['data']['members_count'],
                    "name": item['data']['name'],
                    "photo_50": item['data']['photo_50'],
                    "photo_100": item['data']['photo_100'],
                    "screen_name": item['data']['screen_name'],
                    "photo_200": item['data']['photo_200']
                }
            }
            collections_item.update_one(filter_group, update_data, upsert=True)
        elif item['type'] == 'wall':
            collections_item = self.mongo_base['vk_parse_wall']
            if not collections_item.find_one({'post_id': item['post_id']}):
                collections_item.insert_one(dict(item))
        elif item['type'] == 'update_wall':
            collections_item_wall = self.mongo_base['vk_parse_wall']
            collections_item_group = self.mongo_base['vk_parse_groups']
            if not collections_item_wall.find_one({'post_id': item['post_id']}):
                collections_item_wall.insert_one(dict(item))

            # добавляем средний охват для группы
            last_10_records = collections_item_wall.find().sort([('_id', -1)]).limit(10)
            # Переменная для хранения суммы значений поля
            total_sum = 0

            # Проход по каждой записи
            for record in last_10_records:
                field_views = record.get("views")
                field_group_id = record.get("group_id")

                # Проверка наличия значения и его типа (если нужно)
                if field_views is not None:
                    # Проверка, что значение поля не равно None
                    # Добавление значения поля к общей сумме
                    total_sum += field_views

            filter_group = {"id": abs(field_group_id)}
            update_data = {"$set": {"average_coverage": total_sum // 10}}
            collections_item_group.update_one(filter_group, update_data, upsert=True)
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
            if item['type'] in ('wall', 'update_wall') and "content" in item:
                if item['content']:
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
                                    # картинка поста (устаревший формат)
                                    url_photo = file["posted_photo"]['photo_604']
                                elif file["type"] == "graffiti" and "photo_604" in file["graffiti"]:
                                    # картинка графити (устаревший формат)
                                    url_photo = file["graffiti"]["photo_604"] # 586
                                elif file["type"] == "video" and "image" in file["video"]:
                                    # получаем url обложки видео
                                    big_photo = max(file['video']['image'], key=lambda x: x['width'])
                                    url_photo = big_photo['url']
                                elif file["type"] == "photo" and "sizes" in file["photo"]:
                                    # получаем url самой большой фото
                                    big_photo = max(file['photo']['sizes'], key=lambda x: x['width'])
                                    url_photo = big_photo['url']
                                elif file["type"] == "album" and "thumb" in file["album"]:
                                    # получаем url самой большой фото обложки
                                    big_photo = max(file['album']['thumb']['sizes'], key=lambda x: x['width'])
                                    url_photo = big_photo['url']
                                if file["type"] == "doc" and "preview" in file["doc"]:
                                    big_photo = max(file['doc']['preview']['photo']['sizes'], key=lambda x: x['width'])
                                    url_photo = big_photo['url']
                                elif file["type"] == "link" and "photo" in file["link"]:
                                    big_photo = max(file['link']['photo']['sizes'], key=lambda x: x['width'])
                                    url_photo = big_photo['url']
                                elif file["type"] == "app" and "photo_604" in file["app"]:
                                    # контент приложений (устаревший формат)
                                    url_photo = file['app']['photo_604']
                                elif file["type"] == "poll" and "photo" in file['poll']:
                                    # картинка фона опроса
                                    # if "background" in file['poll']:
                                    #     big_photo = max(file['poll']['background']['images'], key=lambda x: x['width'])
                                    #     url_photo = big_photo['url']
                                    big_photo = max(file['poll']['photo']['images'], key=lambda x: x['width'])
                                    url_photo = big_photo['url']
                                elif file["type"] == "photos_list":
                                    # больше 10 картинок (список)
                                    pass
                                elif file["type"] == "market" and 'thumb_photo' in file['market']:
                                    # картинка обложки товаров и картинки товаров
                                    url_photo = file['market']['thumb_photo']
                                    # big_photo = max(file['market']['photos']['sizes'], key=lambda x: x['width'])
                                    # url_photo = big_photo['url']
                                elif file["type"] == "market_album" and "photo" in file['market_album']:
                                    # картинка обложки альбома
                                    big_photo = max(file['market_album']['photo']['sizes'], key=lambda x: x['width'])
                                    url_photo = big_photo['url']
                                elif file["type"] == "pretty_cards":
                                    big_photo = max(file['pretty_cards']['cards']['images'], key=lambda x: x['width'])
                                    url_photo = big_photo['url']
                                yield scrapy.Request(url_photo)
                            except Exception as e:
                                print(e)
        except KeyError as e:
            print(e)

    def get_images(self, response, request, info, *, item=None):
        for key, image, buf in super().get_images(response, request, info, item=None):
            if not isinstance(buf, BytesIO):
                buf = BytesIO(buf)
            img = Image.open(buf)
            img = img.convert('RGB')

            # Сжимаем изображение
            img_io = BytesIO()
            img.save(img_io, format='JPEG', quality=info.spider.settings.get('IMAGES_JPEG_QUALITY', 90))

            yield key, image, img_io

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
