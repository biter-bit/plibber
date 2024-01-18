import scrapy
from scrapy.http import HtmlResponse
import os
import json
from parse_social_media.items import ParseSocialMediaItemWall
import math
import time
from random import choice


class VkParsePostsSpider6(scrapy.Spider):
    name = "vk_parse_posts_6"
    custom_settings = {
        "NUMBER_OF_ACCOUNT": 6,
        "CONCURRENT_REQUESTS": 3
    }

    def get_list_groups(self, count_groups, count_accounts, number_of_account):
        ending_position = ((count_groups // count_accounts) * number_of_account) + 1  # индекс последнего элемента
        starting_position = (ending_position - (count_groups // count_accounts)) + 1  # индекс первого элемента
        groups_list = list(range(starting_position, ending_position))
        return groups_list

    def get_script_vk_parse_posts(self, group_id, number_iter_posts, ind, number_posts_in_request):
        offset = ind * number_posts_in_request

        vk_script = f"""
        var max_requests = {number_iter_posts};
        var list_response = [];
        var i = 0;
        while (i < max_requests) {{
            var response = API.wall.get({{
                owner_id: {group_id},
                offset: (i * 100) %2B {offset},
                count: 100,
            }});
            list_response.push(response.items);
            i = i %2B 1;
        }}
        return list_response;
        """
        return vk_script.replace('\n', ' ')

    def start_requests(self):
        number_of_account = self.settings['NUMBER_OF_ACCOUNT']  # номер аккаунта
        count_groups = int(os.getenv('COUNT_GROUPS'))  # кол-во групп, которые нужно обработать
        count_accounts = int(os.getenv('COUNT_SPIDERS'))  # кол-во включенных процессов (аккаунтов, пауков)

        token = choice(os.getenv('ACCOUNT_TOKENS').split(','))  # рабочий токен

        groups_list = self.get_list_groups(count_groups, count_accounts, number_of_account)  # итоговый список

        for group_id in groups_list:
            url_posts = (f'https://api.vk.com/method/wall.get?access_token={token}&owner_id={-group_id}&count=1&v=5.154')
            yield scrapy.Request(
                url=url_posts,
                callback=self.parse,
                meta={'group_id': group_id, 'token': token, 'type': 'post'}
            )

    def parse(self, response: HtmlResponse):
        # ответ в формате словаря
        response_json = response.json()
        # рабочий токен
        token_account = response.meta['token']

        # получение постов

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
        # кол-во всех запросов внутри execute (int)
        number_of_requests = math.ceil(count_posts / 100)
        # кол-во запросов execute (int)
        number_total_requests = math.ceil(number_of_requests / 25)
        # обрабатываемая группа
        group_id = response.meta['group_id']
        # кол-во постов за 1 запрос execute
        number_posts_in_request = count_posts // number_total_requests
        # кол-во запросов за 1 execute
        number_iter_posts = math.ceil(number_posts_in_request/100)

        for i in range(0, number_total_requests):
            vk_script = self.get_script_vk_parse_posts(-group_id, number_iter_posts, i, number_posts_in_request)
            url = f'https://api.vk.com/method/execute?access_token={token_account}&code={vk_script}&v=5.154'
            yield response.follow(url, callback=self.posts_preparetion)

    def posts_preparetion(self, response: HtmlResponse):
        wall_data = json.loads(response.text)
        try:
            result_groups_data = sum(wall_data['response'], [])
        except KeyError:
            self.logger.debug(f'Got wall_data: {wall_data}')
        yield ParseSocialMediaItemWall(type='wall', data=result_groups_data)
