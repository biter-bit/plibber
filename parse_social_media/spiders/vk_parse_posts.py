import scrapy
from scrapy.http import HtmlResponse
import os
import json
from parse_social_media.items import ParseSocialMediaItemWall
import math


class VkParsePostsSpider(scrapy.Spider):
    name = "vk_parse_posts_1"

    def __init__(self, number_of_account=None, number_of_groups=None, name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.number_of_account = number_of_account
        self.number_of_groups = number_of_groups
        self.name = name

    def get_list_groups(self, count_groups, count_process, number_of_group, count_groups_spiders):
        ending_position = count_groups // count_process // count_groups_spiders * number_of_group + 1  # индекс последнего элемента
        starting_position = ending_position - count_groups // count_process // count_groups_spiders # индекс первого элемента
        groups_list = list(range(starting_position, ending_position))
        return groups_list

    def get_script_vk_parse_posts(self, group_id, ind, number_posts_in_request):
        offset = ind * number_posts_in_request

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
            "comments": []
        }};
        var i = 0;
        while (i < max_requests) {{
            var response = API.wall.get({{
                owner_id: {group_id},
                offset: (i * 100) + {offset},
                count: 100,
            }});
            var result = {{'post_id': response.items@.id, 'group_id': response.items@.from_id, 'hash_post': response.items@.hash, 'text': response.items@.text, 'photo': response.items@.attachments, 'market_as_ads':  response.items@.marked_as_ads, 'views':  response.items@.views@.count, 'likes': response.items@.likes@.count, 'reposts': response.items@.reposts@.count, 'comments': response.items@.comments@.count}};
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
            delete response;
            delete result;
            i = i + 1;
        }}
        return list_response;
        """
        return vk_script.replace('\n', ' ')

    def start_requests(self):
        number_of_account = self.number_of_account
        number_of_groups = self.number_of_groups
        count_groups = int(os.getenv('COUNT_GROUPS'))  # кол-во групп, которые нужно обработать
        count_process = int(os.getenv('COUNT_PROCESS'))  # кол-во включенных процессов (аккаунтов, пауков)
        count_groups_spiders = int(os.getenv('COUNT_GROUPS_SPIDERS'))

        token = os.getenv('ACCOUNT_TOKENS').split(',')[number_of_account-1]  # рабочий токен

        # with open('config.json', 'a') as config_file:
        #     config_file.write(token)

        groups_list = self.get_list_groups(count_groups, count_process, number_of_groups, count_groups_spiders)  # итоговый список

        for group_id in groups_list:
            url_posts = f'https://api.vk.com/method/wall.get?access_token={token}&owner_id={-group_id}&count=1&v=5.154'
            yield scrapy.Request(
                url=url_posts,
                callback=self.parse,
                meta={'group_id': group_id, 'token': token}
            )

    def parse(self, response: HtmlResponse):
        # ответ в формате словаря
        response_json = response.json()
        # рабочий токен
        token_account = response.meta['token']
        # обрабатываемая группа
        group_id = response.meta['group_id']

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

        # кол-во постов в группе
        count_posts = response_json['response']['count']

        try:
            count_posts = response_json['response']['count']
        except KeyError as er:
            print(er)
            with open('configs.json', 'a') as config_file:
                config_file.write("error: {}\ntoken: {}".format(response_json, token_account))

        # кол-во постов за 1 запрос execute
        count_posts_for_execute = 25 * 100  # второе число заменить
        # всего execute запросов
        total_execute_requests = math.ceil(count_posts / count_posts_for_execute)

        for i in range(0, total_execute_requests):
            vk_script = self.get_script_vk_parse_posts(-group_id, i, count_posts_for_execute)
            url = f'https://api.vk.com/method/execute'
            yield scrapy.FormRequest(
                url,
                callback=self.posts_preparetion,
                formdata={
                    'access_token': token_account,
                    'code': vk_script,
                    'v': "5.154"
                }
            )

    def posts_preparetion(self, response: HtmlResponse):
        wall_data = json.loads(response.text)
        wall_response = wall_data['response']
        try:
            for post in range(len(wall_response['post_id'])):
                post_id = wall_response['post_id'][post]
                group_id = wall_response['group_id'][post]
                hash_post = wall_response['hash_post'][post]
                text = wall_response['text'][post]
                photo = wall_response['photo'][post]
                market_as_ads = wall_response['market_as_ads'][post]
                views = wall_response['views'][post]
                likes = wall_response['likes'][post]
                comments = wall_response['comments'][post]
                # result_groups_data = sum(wall_data['response'], [])
                yield ParseSocialMediaItemWall(
                    type='wall',
                    post_id=post_id,
                    group_id=group_id,
                    hash_post=hash_post,
                    text=text,
                    photo=photo,
                    market_as_ads=market_as_ads,
                    views=views,
                    likes=likes,
                    comments=comments
                )
        except KeyError:
            self.logger.debug(f'Got wall_data: {wall_data}')
