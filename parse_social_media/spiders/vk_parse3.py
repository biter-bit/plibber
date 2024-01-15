import scrapy
from scrapy.http import HtmlResponse
import os
import json
from parse_social_media.items import ParseSocialMediaItem
import math


class VkParse3Spider(scrapy.Spider):
    name = "vk_parse3"
    start_urls = ["https://vk.com"]

    custom_settings = {
        "NUMBER_OF_ACCOUNT": 3,
    }

    # def calculate_account_range(self, count_groups, count_accounts, idx):
    #     range_id_end = count_groups // count_accounts * idx
    #     range_id_start = range_id_end - (count_groups // count_accounts)
    #     result_list = list(range(range_id_start + 1, range_id_end + 1))
    #     return result_list

    def start_requests(self):
        number_of_account = self.settings['NUMBER_OF_ACCOUNT']
        count_groups = int(os.getenv('COUNT_GROUPS'))
        count_accounts = int(os.getenv('COUNT_SPIDERS'))
        token = os.getenv('ACCOUNT_TOKENS').split(',')[number_of_account - 1]

        ending_position = ((count_groups // count_accounts) * number_of_account) + 1
        starting_position = (ending_position - (count_groups // count_accounts)) + 1

        result_list_groups = list(range(starting_position, ending_position))

        yield scrapy.FormRequest(
            url='https://api.vk.com/method/groups.getById',
            formdata={
                'access_token': token,
                'v': '5.154',
                'group_ids': "1",
                'fields': 'can_see_all_posts,members_count',
            },
            callback=self.parse,
            meta={'range_id': result_list_groups, 'token': token}
        )

    def parse(self, response: HtmlResponse):
        # список групп (list)
        range_ids = response.meta['range_id']
        # кол-во всех запросов (int)
        number_of_requests = math.ceil(len(range_ids)/380)
        # кол-во запросов в общем (int)
        number_total_requests = math.ceil(number_of_requests/25)
        # по сколько групп на каждый внутренний запрос (int)
        number_iter_groups = len(range_ids)//number_total_requests

        token_account = response.meta['token']
        for i in range(0, number_total_requests):
            # первая пачка групп для запроса
            groups_id_list_vk_parse = range_ids[i * number_iter_groups:i * number_iter_groups + number_iter_groups]
            length_groups = len(groups_id_list_vk_parse)
            max_requests = math.ceil(length_groups/380)

            groups_id_str_vk_parse = str(groups_id_list_vk_parse)
            vk_script = """
    var groups_id_list = %s;
    var max_requests = %s;
    var list_response = [];
    var i = 0;
    while (i < max_requests) {
        var start_idx = i * 380;
        var end_idx = start_idx + 380;
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
        result_groups_data = sum(groups_data['response'], [])
        yield ParseSocialMediaItem(groups_data=result_groups_data)
