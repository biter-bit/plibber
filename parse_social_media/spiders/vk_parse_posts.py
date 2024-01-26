import scrapy
from scrapy.http import HtmlResponse
import os
import json
from parse_social_media.items import ParseSocialMediaItemWall
import math
from parse_social_media.custom_exception import Error29Exception, Error13Exception, Error6Exception
from parse_social_media.service import error
from datetime import datetime, timedelta
from scrapy.exceptions import CloseSpider


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
        var result = {{'post_id': response.items@.id, 'group_id': response.items@.owner_id, 
            'hash_post': response.items@.hash, 'text': response.items@.text, 'photo': response.items@.attachments, 
            'market_as_ads':  response.items@.marked_as_ads, 'views':  response.items@.views@.count, 
            'likes': response.items@.likes@.count, 'reposts': response.items@.reposts@.count, 
            'comments': response.items@.comments@.count, 'date': response.items@.date
        }};
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
    }}
    return list_response;
    """
    return vk_script.replace('\n', ' ')


def get_list_groups(count_groups, count_process, number_of_group, count_groups_spiders):
    """Возвращает список групп для указанного номера паука"""

    # индекс последнего элемента
    ending_position = count_groups // count_process // count_groups_spiders * number_of_group + 1
    # индекс первого элемента
    starting_position = ending_position - count_groups // count_process // count_groups_spiders
    groups_list = list(range(starting_position, ending_position))
    return groups_list


class VkParsePostsSpider(scrapy.Spider):
    name = "vk_parse_posts_1"

    def __init__(self, number_of_account=None, number_of_groups=None, name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

        # рабочий токен
        self.token = os.getenv('ACCOUNT_TOKENS').split(',')[number_of_account - 1]

        self.number_of_account = number_of_account
        self.number_of_groups = number_of_groups
        self.groups_list = None
        self.error = 'done'

        self.group_id = None
        self.offset = None

        # кол-во групп, которые нужно обработать
        self.count_groups = int(os.getenv('COUNT_GROUPS'))

        # кол-во включенных процессов (аккаунтов, пауков)
        self.count_process = int(os.getenv('COUNT_PROCESS'))

        self.count_groups_spiders = int(os.getenv('COUNT_GROUPS_SPIDERS'))
        self.list_errors = []

    def start_requests(self):
        # итоговый список
        self.groups_list = get_list_groups(
            self.count_groups,
            self.count_process,
            self.number_of_groups,
            self.count_groups_spiders
        )
        self.group_id = self.groups_list[0]

        for group_id in self.groups_list:
            self.group_id = group_id
            url_posts = (f'https://api.vk.com/method/wall.get?'
                         f'access_token={self.token}&owner_id={-self.group_id}&count=1&v=5.154')
            yield scrapy.Request(url=url_posts, callback=self.parse)

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

            # общее кол-во постов в группе
            count_posts = response_json['response']['count']
            # кол-во постов за 1 запрос execute
            count_posts_for_execute = 25 * 25  # второе число заменить
            # всего execute запросов
            total_execute_requests = math.ceil(count_posts / count_posts_for_execute)

            for i in range(0, total_execute_requests):
                self.offset = i * count_posts_for_execute
                vk_script = get_script_vk_parse_posts(-self.group_id, self.offset)
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
                        'token': self.token
                    }
                )

        except Error6Exception:
            self.error = 6
            self.list_errors.append({
                "group_id": self.group_id,
                "offset": self.offset,
                "error": self.error
            })

        except Error13Exception:
            self.error = 13
            self.list_errors.append({
                "group_id": self.group_id,
                "offset": self.offset,
                "error": self.error
            })

        except Error29Exception:
            self.error = 29
            self.list_errors.append({
                "group_id": self.group_id,
                "offset": self.offset,
                "error": self.error
            })

    def posts_preparetion(self, response: HtmlResponse):
        wall_data = json.loads(response.text)
        try:
            # вызываем raise если есть ошибки 6, 13, 29
            error(wall_data)

            wall_response = wall_data['response']
            for post in range(len(wall_response['post_id'])):
                post_id = wall_response['post_id'][post]
                group_id = wall_response['group_id'][post]
                hash_post = wall_response['hash_post'][post]
                text = wall_response['text'][post]
                photo = wall_response['photo'][post]
                marked_as_ads = wall_response['market_as_ads'][post]
                views = wall_response['views'][post]
                likes = wall_response['likes'][post]
                comments = wall_response['comments'][post]
                reposts = wall_response['reposts'][post]
                date = wall_response['date'][post]
                # result_groups_data = sum(wall_data['response'], [])
                yield ParseSocialMediaItemWall(
                    type='wall',
                    post_id=post_id,
                    group_id=group_id,
                    hash_post=hash_post,
                    text=text,
                    photo=photo,
                    marked_as_ads=marked_as_ads,
                    views=views,
                    likes=likes,
                    comments=comments,
                    reposts=reposts,
                    date=date
                )

        except Error6Exception:
            self.error = 6
            self.list_errors.append({
                "group_id": self.group_id,
                "offset": self.offset,
                "error": self.error
            })

        except Error13Exception:
            self.error = 13
            self.list_errors.append({
                "group_id": self.group_id,
                "offset": self.offset,
                "error": self.error
            })

        except Error29Exception:
            self.error = 29
            self.list_errors.append({
                "group_id": self.group_id,
                "offset": self.offset,
                "error": self.error
            })

    def close(self, reason):
        # получение текущей даты и времени
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime("%d/%m/%Y %H:%M:%S")

        # получение даты и времени через 24 часа
        new_datetime = current_datetime + timedelta(hours=24)
        formatted_new_datetime = new_datetime.strftime("%d/%m/%Y %H:%M:%S")

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
