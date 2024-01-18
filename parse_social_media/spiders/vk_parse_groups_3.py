import scrapy
from scrapy.http import HtmlResponse
import os
import json
from parse_social_media.items import ParseSocialMediaItem
import math
from random import choice


class VkParseGroupSpider3(scrapy.Spider):
    name = "vk_parse_group_3"
    custom_settings = {
        "NUMBER_OF_ACCOUNT": 3,
    }

    def get_list_groups(self, count_groups, count_accounts, number_of_account):
        ending_position = ((count_groups // count_accounts) * number_of_account) + 1  # индекс последнего элемента
        starting_position = ((ending_position - 1) - (count_groups // count_accounts))  # индекс первого элемента
        groups_list = list(range(starting_position, ending_position))
        return groups_list

    def get_script_vk_parse_groups(self, ind, groups_list, number_iter_groups):
        groups_id_list_vk_parse = groups_list[ind * number_iter_groups:ind * number_iter_groups + number_iter_groups]
        length_groups = len(groups_id_list_vk_parse)
        max_requests = math.ceil(length_groups / 350)

        groups_id_str_vk_parse = str(groups_id_list_vk_parse)
        vk_script = f"""
    var groups_id_list = {groups_id_str_vk_parse};
    var max_requests = {max_requests};
    var list_response = [];
    var i = 0;
    while (i < max_requests) {{
        var start_idx = i * 350;
        var end_idx = start_idx + 350;
        var groups_str = groups_id_list.slice(start_idx, end_idx);
        var response = API.groups.getById({{
            group_ids: groups_str,
        }});
        list_response.push(response.groups);
        i = i + 1;
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

        url_groups = (f'https://api.vk.com/method/groups.getById?access_token={token}&v=5.154&group_ids=1&fields=can_see_all_posts,members_count')

        yield scrapy.Request(
            url=url_groups,
            callback=self.parse,
            meta={'groups_list': groups_list, 'token': token, 'type': 'group'}
        )

    def parse(self, response: HtmlResponse):
        # ответ в формате словаря
        response_json = response.json()
        # рабочий токен
        token_account = response.meta['token']

        # список групп (list)
        groups_list = response.meta['groups_list']
        # кол-во всех запросов (int)
        number_of_requests = math.ceil(len(groups_list) / 350)
        # кол-во запросов в общем (int)
        number_total_requests = math.ceil(number_of_requests / 25)
        # по сколько групп на каждый внутренний запрос (int)
        number_iter_groups = len(groups_list) // number_total_requests

        # получение групп

        if response.meta['type'] == 'group':
            for i in range(0, number_total_requests):
                vk_script = self.get_script_vk_parse_groups(i, groups_list, number_iter_groups)
                url = f'https://api.vk.com/method/execute'
                yield scrapy.FormRequest(
                    url=url,
                    method='POST',
                    callback=self.groups_preparetion,
                    formdata={'access_token': token_account, 'code': vk_script, 'v': "5.154"},
                    meta={'token': token_account})

    def groups_preparetion(self, response: HtmlResponse):
        groups_data = json.loads(response.text)
        result_groups_data = sum(groups_data['response'], [])
        yield ParseSocialMediaItem(type='group', data=result_groups_data)
