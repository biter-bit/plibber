import scrapy
from scrapy.http import HtmlResponse
import os
import json
from parse_social_media.items import ParseSocialMediaItemWall
import math
from parse_social_media.custom_exception import Error29Exception, Error13Exception, Error6Exception
from parse_social_media.service import error
from datetime import datetime, timedelta
from parse_social_media.spiders.vk_parse_groups import get_list_groups
from scrapy.exceptions import CloseSpider
from scrapy.loader import ItemLoader


def get_script_vk_parse_posts(group_id, offset):
    """Создает скрипт для запроса execute к vk api"""

    vk_script = f"""
    var max_requests = 25;
    var list_response = {{
        "post_id": [],
        "group_id": [],
        "hash_post": [],
        "text": [],
        "photo": [],
        "market_as_ads": [],
        "views": [],
        "likes": [],
        "reposts": [],
        "comments": [],
        "date": []
    }};
    var i = 0;
    while (i < max_requests) {{
        var response = API.wall.get({{
            owner_id: {group_id},
            offset: (i * 25) + {offset},
            count: 25,
        }});
        if (response.items) {{
            var result = {{'post_id': response.items@.id, 'group_id': response.items@.owner_id, 'hash_post': response.items@.hash, 'text': response.items@.text, 'photo': response.items@.attachments, 'market_as_ads':  response.items@.marked_as_ads, 'views':  response.items@.views@.count, 'likes': response.items@.likes@.count, 'reposts': response.items@.reposts@.count, 'comments': response.items@.comments@.count, 'date': response.items@.date}};
            list_response.post_id = list_response.post_id + result.post_id;
            list_response.group_id = list_response.group_id + result.group_id;
            list_response.hash_post = list_response.hash_post + result.hash_post;
            list_response.reposts = list_response.reposts + result.reposts;
            list_response.photo = list_response.photo + result.photo;
            list_response.market_as_ads = list_response.market_as_ads + result.market_as_ads;
            list_response.views = list_response.views + result.views;
            list_response.likes = list_response.likes + result.likes;
            list_response.text = list_response.text + result.text;
            list_response.comments = list_response.comments + result.comments;
            list_response.date = list_response.date + result.date;
            delete response;
            delete result;
            i = i + 1;
        }} else {{
            delete response;
            i = i + 1;
        }};
    }}
    return list_response;
    """
    return vk_script.replace('\n', ' ')


class VkParsePostsSpider(scrapy.Spider):
    name = "vk_parse_posts_1"

    def __init__(self, number_of_account=None, number_of_groups=None, name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

        # рабочий токен
        self.token = os.getenv('ACCOUNT_TOKENS').split(',')[number_of_account - 1]

        # итоговый список
        # self.groups_list = list(range(int(os.getenv('START_IDX_GROUP')), int(os.getenv('END_IDX_GROUP'))))
        self.group = None

        # кол-во групп, которые нужно обработать
        self.count_groups = int(os.getenv('END_IDX_GROUP')) - int(os.getenv('START_IDX_GROUP'))

        # кол-во включенных процессов (аккаунтов, пауков)
        self.count_process = int(os.getenv('COUNT_PROCESS'))
        self.count_groups_spiders = int(os.getenv('COUNT_GROUPS_SPIDERS'))

        self.offset = None
        self.count_posts = None
        self.list_errors = []
        self.error = 'done'

        # итоговый список
        self.groups_list = get_list_groups(
            int(os.getenv('START_IDX_GROUP')),
            int(os.getenv('END_IDX_GROUP')),
            self.count_groups_spiders,
            self.count_process,
            number_of_groups
        )

    def start_requests(self):
        offset_group = int(os.getenv('PASS_POSTS_IN_GROUPS'))
        for group_id in self.groups_list:
            self.group = group_id
            self.offset = None
            url_posts = (f'https://api.vk.com/method/wall.get?'
                         f'access_token={self.token}&owner_id={-group_id}&offset={offset_group}&count=1&v=5.154')
            yield scrapy.Request(
                url=url_posts,
                callback=self.parse,
                meta={
                    'group_id': group_id,
                    'offset_group': offset_group
                }
            )

    def parse(self, response: HtmlResponse):
        # ответ в формате словаря
        response_json = response.json()

        # исключаем закрытые, с закрытой стеной, заблокированные группы
        if 'error' in response_json:
            error_msg = response_json['error']['error_msg']

            access_denied_errors = [
                'Access denied: wall is disabled',
                'Access denied: group is blocked',
                'Access denied: this wall available only for community members'
            ]

            if any(error_msg in error_text for error_text in access_denied_errors):
                return

        try:
            # вызываем raise если есть ошибки 6, 13, 29
            error(response_json)

            # проверка на наличие постов
            if not response_json['response']['items']:
                return

            group_id = response.meta['group_id']
            # кол-во постов, которое нужно пропустить в группе
            offset_group_start = response.meta['offset_group']
            # общее кол-во постов в группе
            count_posts = response_json['response']['count'] - offset_group_start
            # кол-во постов за 1 запрос execute
            count_posts_for_execute = 25 * 25  # второе число заменить
            self.count_posts = count_posts_for_execute
            # всего execute запросов
            total_execute_requests = math.ceil(count_posts / count_posts_for_execute)

            for i in range(0, total_execute_requests):
                self.group = group_id
                offset_group = i * count_posts_for_execute + offset_group_start
                self.offset = offset_group
                vk_script = get_script_vk_parse_posts(-group_id, offset_group)
                url = f'https://api.vk.com/method/execute'
                yield scrapy.FormRequest(
                    url,
                    callback=self.posts_preparetion,
                    formdata={
                        'access_token': self.token,
                        'code': vk_script,
                        'v': "5.154"
                    },
                    meta={
                        'group_id': group_id,
                        'offset_group': offset_group,
                        'count_posts': count_posts_for_execute
                    }
                )

        except Error6Exception:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "offset_user": int(os.getenv('PASS_POSTS_IN_GROUPS')),
                "error": 6,
            })

        except Error13Exception:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "offset_user": int(os.getenv('PASS_POSTS_IN_GROUPS')),
                "error": 13,
            })

        except Error29Exception:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "offset_user": int(os.getenv('PASS_POSTS_IN_GROUPS')),
                "error": 29,
            })

        except Exception as e:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "offset_user": int(os.getenv('PASS_POSTS_IN_GROUPS')),
                "error": 500,
            })

    def posts_preparetion(self, response: HtmlResponse):
        wall_data = json.loads(response.text)
        try:
            # вызываем raise если есть ошибки 6, 13, 29
            error(wall_data)
            wall_response = wall_data['response']

            for post in range(len(wall_response['post_id'])):
                yield ParseSocialMediaItemWall(
                    type='wall',
                    post_id=wall_response['post_id'][post],
                    group_id=wall_response['group_id'][post],
                    hash_post=wall_response['hash_post'][post],
                    text=wall_response['text'][post],
                    content=wall_response['photo'][post],
                    marked_as_ads=wall_response['market_as_ads'][post],
                    views=wall_response['views'][post],
                    likes=wall_response['likes'][post],
                    comments=wall_response['comments'][post],
                    reposts=wall_response['reposts'][post],
                    date=wall_response['date'][post]
                )

            # for post in range(len(wall_response['post_id'])):
            #     loader = ItemLoader(item=ParseSocialMediaItemWall(), response=response)
            #     loader.add_value('post_id', wall_response['post_id'][post])
            #     loader.add_value('group_id', wall_response['group_id'][post])
            #     loader.add_value('hash_post', wall_response['hash_post'][post])
            #     loader.add_value('text', wall_response['text'][post])
            #     loader.add_value('content', wall_response['photo'][post])
            #     loader.add_value('marked_as_ads', wall_response['market_as_ads'][post])
            #     loader.add_value('views', wall_response['views'][post])
            #     loader.add_value('likes', wall_response['likes'][post])
            #     loader.add_value('comments', wall_response['comments'][post])
            #     loader.add_value('reposts', wall_response['reposts'][post])
            #     loader.add_value('date', wall_response['date'][post])
            #     loader.add_value('photo', None)
            #     loader.add_value('type', 'wall')
            #     yield loader.load_item()

        except Error6Exception:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "offset_user": int(os.getenv('PASS_POSTS_IN_GROUPS')),
                "offset": response.meta['offset_group'],
                'count_posts': response.meta['count_posts'],
                "error": 6,
            })

        except Error13Exception:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "offset_user": int(os.getenv('PASS_POSTS_IN_GROUPS')),
                "offset": response.meta['offset_group'],
                'count_posts': response.meta['count_posts'],
                "error": 13,
            })

        except Error29Exception:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "offset_user": int(os.getenv('PASS_POSTS_IN_GROUPS')),
                "offset": response.meta['offset_group'],
                'count_posts': response.meta['count_posts'],
                "error": 29,
            })

        except Exception as e:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "offset_user": int(os.getenv('PASS_POSTS_IN_GROUPS')),
                "offset": response.meta['offset_group'],
                'count_posts': response.meta['count_posts'],
                "error": 500,
            })

    def close(self, reason):
        # получение текущей даты и времени
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime("%d/%m/%Y %H:%M:%S")

        # получение даты и времени через 24 часа
        new_datetime = current_datetime + timedelta(hours=24)
        formatted_new_datetime = new_datetime.strftime("%d/%m/%Y %H:%M:%S")

        if reason == 'closespider_pagecount':
            self.list_errors.append({
                "group_id": self.group,
                "offset_user": int(os.getenv('PASS_POSTS_IN_GROUPS')),
                "offset": self.offset,
                'count_posts': self.count_posts,
                "error": 202,
            })

        if reason == 'finish':
            self.list_errors.append({
                "group_id": self.group,
                "offset_user": int(os.getenv('PASS_POSTS_IN_GROUPS')),
                "offset": self.offset,
                'count_posts': self.count_posts,
                "error": 200,
            })

        # создание словаря, который будет в файле
        date_to_save = {
            self.name: {
                "token": self.token,
                "date_finish": formatted_date,
                "reboot_date": formatted_new_datetime,
                "result": self.list_errors
            }
        }

        # создание файла (чтение)
        existing_file_path = f'data/error_posts.json'
        try:
            # Прочитать данные из существующего файла
            with open(existing_file_path, 'r') as json_file:
                existing_data = json.load(json_file)
        except json.decoder.JSONDecodeError:
            print(f"Error decoding JSON in {existing_file_path}. Creating a new empty dictionary.")
            existing_data = {}
        except FileNotFoundError:
            print(f"File {existing_file_path} not found. Creating a new empty dictionary.")
            existing_data = {}

        # создание файла (запись)
        existing_data.update(date_to_save)
        with open(existing_file_path, 'w') as file:
            json.dump(existing_data, file, indent=4)
