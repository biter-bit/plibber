import scrapy
from scrapy.http import HtmlResponse
import os
import json
from parse_social_media.items import ParseSocialMediaItem
import math


class VkParseSpider(scrapy.Spider):
    name = "vk_parse_groups"
    start_urls = ['https://vk.com/']
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

    def parse(self, response: HtmlResponse):
        # список групп (list)
        range_ids = response.meta['range_id']
        # кол-во всех запросов (int)
        number_of_requests = math.ceil(len(range_ids)/370)
        # кол-во запросов в общем (int)
        number_total_requests = math.ceil(number_of_requests/25)
        # по сколько групп на каждый внутренний запрос (int)
        number_iter_groups = len(range_ids)//number_total_requests

        token_account = response.meta['token']
        for i in range(0, number_total_requests):
            # первая пачка групп для запроса
            groups_id_list_vk_parse = range_ids[i * number_iter_groups:i * number_iter_groups + number_iter_groups]
            length_groups = len(groups_id_list_vk_parse)
            max_requests = math.ceil(length_groups/370)

            groups_id_str_vk_parse = str(groups_id_list_vk_parse)
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
