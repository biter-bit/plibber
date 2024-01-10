import scrapy
from scrapy.http import HtmlResponse
from dotenv import load_dotenv
import os
import random
import json
from parse_social_media.items import ParseSocialMediaItem
import time
import math


class VkParseSpider(scrapy.Spider):
    name = "vk_parse_groups"
    start_urls = ['https://vk.com/']
    tokens = os.getenv(f"VK_ACCESS_TOKEN").split(',')
    result_tokens = []

    def calculate_account_range(self, count_groups, count_accounts, idx):
        range_id_end = count_groups // count_accounts * idx
        range_id_start = range_id_end - (count_groups // count_accounts)
        result_list = list(range(range_id_start + 1, range_id_end + 1))
        return result_list

    def start_requests(self):
        count_groups = int(os.getenv("COUNT_GROUPS"))
        count_accounts = int(os.getenv("COUNT_ACCOUNTS"))
        tokens = os.getenv(f"VK_ACCESS_TOKEN").split(',')

        for idx in range(1, count_accounts + 1):
            result_string = self.calculate_account_range(count_groups, count_accounts, idx)
            token = tokens[idx-1]

            yield scrapy.FormRequest(
                url='https://api.vk.com/method/groups.getById',
                formdata={
                    'access_token': token,
                    'v': '5.154',
                    'group_ids': str(idx),
                    'fields': 'can_see_all_posts,members_count',
                },
                callback=self.parse,
                meta={'range_id': result_string, 'token': token}
            )

    # def check_token_account(self, response: HtmlResponse):
    #     response_json = response.json()
    #
    #     if 'error' not in response_json:
    #         self.result_tokens.append(self.tokens[0])
    #
    #     for token in self.tokens[1:]:
    #         yield response.follow(
    #             url=f'https://api.vk.com/method/user.get?access_token={token}&v=5.154&user_ids=1',
    #             callback=self.check_token_list,
    #             meta={'token': token}
    #         )
    #     yield from self.start_requests()
    #
    # def check_token_list(self, response: HtmlResponse):
    #     response_json = response.json()
    #
    #     if 'error' not in response_json:
    #         self.result_tokens.append(response.meta['token'])

    def parse(self, response: HtmlResponse):
        # список групп (list)
        range_ids = response.meta['range_id']
        # кол-во всех запросов (int)
        number_of_requests = math.ceil(len(range_ids)/350)
        # кол-во запросов в общем (int)
        number_total_requests = math.ceil(number_of_requests/25)
        # по сколько групп на каждый внутренний запрос (int)
        number_iter_groups = len(range_ids)//number_total_requests

        token_account = response.meta['token']
        for i in range(0, number_total_requests):
            # первая пачка групп для запроса
            groups_id_list_vk_parse = range_ids[i * number_iter_groups:i * number_iter_groups + number_iter_groups]
            length_groups = len(groups_id_list_vk_parse)
            max_requests = math.ceil(length_groups/350)

            groups_id_str_vk_parse = str(groups_id_list_vk_parse)
            # group_id_str = ','.join(map(str, range_ids[i * 500:i * 500 + 500]))
            vk_script = """
    var groups_id_list = %s;
    var max_requests = %s;
    var list_response = [];
    var i = 0;
    while (i < max_requests) {
        var start_idx = i * 500;
        var end_idx = start_idx + 500;
        var groups_str = groups_id_list.slice(start_idx, end_idx);
        var response = API.groups.getById({
            group_ids: groups_str,
        });
        list_response.push(response.groups);
        i = i + 1;
    }
    return list_response;
            """%(groups_id_str_vk_parse, max_requests)
            yield scrapy.FormRequest(
                url='https://api.vk.com/method/execute',
                method='POST',
                formdata={
                    'access_token': token_account,
                    'code': vk_script,
                    'v': '5.154',
                },
                callback=self.transfer
            )

    def transfer(self, response: HtmlResponse):
        groups_data = json.loads(response.text)
        yield ParseSocialMediaItem(groups_data=groups_data['response'])
