import scrapy
from scrapy.http import HtmlResponse
import os
import json
from parse_social_media.items import ParseSocialMediaItemWall, ParseSocialMediaItem
from parse_social_media.custom_exception import Error29Exception, Error13Exception, Error6Exception
from parse_social_media.service import error
from datetime import datetime, timedelta
from parse_social_media.spiders.vk_parse_posts import get_list_groups


class VkParseUpdateSpider(scrapy.Spider):
    name = "vk_parse_update_1"

    def __init__(self, number_of_account=None, number_of_groups=None, name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

        # рабочий токен
        self.token = os.getenv('ACCOUNT_TOKENS').split(',')[number_of_account - 1]

        self.error = 'done'

        self.count_groups = int(os.getenv('END_IDX_GROUP')) - int(os.getenv('START_IDX_GROUP'))  # кол-во групп, которые нужно обработать

        # кол-во включенных процессов (аккаунтов, пауков)
        self.count_process = int(os.getenv('COUNT_PROCESS'))

        self.count_groups_spiders = int(os.getenv('COUNT_GROUPS_SPIDERS'))
        self.list_errors = []

        self.group = None

        # итоговый список
        self.groups_list = get_list_groups(
            int(os.getenv('START_IDX_GROUP')),
            int(os.getenv('END_IDX_GROUP')),
            self.count_groups_spiders,
            self.count_process,
            number_of_groups
        )

    def start_requests(self):

        for group_id in self.groups_list:
            self.group = group_id
            url_posts = (f'https://api.vk.com/method/wall.get?'
                         f'access_token={self.token}&owner_id={-group_id}&count=50&v=5.154')
            yield scrapy.Request(url=url_posts, callback=self.parse, meta={'group_id': group_id, 'update_group': True})

    def parse(self, response: HtmlResponse):
        update_group = response.meta['update_group']
        if update_group:
            response.meta['update_group'] = False
            group = response.meta['group_id']
            url_groups = (f'https://api.vk.com/method/groups.getById?'
                          f'access_token={self.token}&v=5.154&group_ids={group}&fields=can_see_all_posts,members_count')
            yield response.follow(
                url=url_groups,
                callback=self.parse_group,
            )

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

            wall_response = response_json['response']['items']
            for post in wall_response:
                post_id = post['id']
                group_id = abs(post['owner_id'])
                hash_post = post['hash']
                text = post['text']
                photo = post['attachments']
                marked_as_ads = post['marked_as_ads']
                views = post.get('views', {}).get('count')
                likes = post.get('likes', {}).get('count')
                comments = post.get('comments', {}).get('count')
                reposts = post.get('reposts', {}).get('count')
                date = post['date']
                # result_groups_data = sum(wall_data['response'], [])
                yield ParseSocialMediaItemWall(
                    type='update_wall',
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
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "error": 6
            })

        except Error13Exception:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "error": 13
            })

        except Error29Exception:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "error": 29
            })

        except Exception as e:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "error": 500
            })

    def parse_group(self, response: HtmlResponse):
        try:
            content_group = response.json()['response']['groups'][0]
            yield ParseSocialMediaItem(
                type='update_group',
                data=content_group
            )
        except Error6Exception:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "error": 6
            })

        except Error13Exception:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "error": 13
            })

        except Error29Exception:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "error": 29
            })

        except Exception as e:
            self.list_errors.append({
                "group_id": response.meta['group_id'],
                "error": 500
            })

    def close(self, reason):
        # получение текущей даты и времени
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime("%d/%m/%Y %H:%M:%S")

        # получение даты и времени через 24 часа
        new_datetime = current_datetime + timedelta(hours=24)
        formatted_new_datetime = new_datetime.strftime("%d/%m/%Y %H:%M:%S")

        if reason == 'finish':
            self.list_errors.append({
                "group_id": self.group,
                "error": 200
            })

        if reason == 'closespider_pagecount':
            self.list_errors.append({
                "group_id": self.group,
                "error": 202
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
        existing_file_path = f'data/error_update.json'
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
