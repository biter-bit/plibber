import scrapy
from scrapy.http import HtmlResponse
import os
import json
from parse_social_media.items import ParseSocialMediaItem
import math


class VkParseGroupSpider(scrapy.Spider):
    name = "vk_parse_group_1"

    def __init__(self, number_of_account=None, number_of_groups=None, name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.number_of_account = number_of_account
        self.number_of_groups = number_of_groups
        self.name = name

    def get_list_groups(self, count_groups, count_process, number_of_group, count_groups_spiders):
        ending_position = count_groups // count_process // count_groups_spiders * number_of_group + 1  # индекс последнего элемента
        starting_position = ending_position - count_groups // count_process // count_groups_spiders  # индекс первого элемента
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
        number_of_account = self.number_of_account
        number_of_groups = self.number_of_groups  # номер аккаунта
        count_groups = int(os.getenv('COUNT_GROUPS'))  # кол-во групп, которые нужно обработать
        count_process = int(os.getenv('COUNT_PROCESS'))  # кол-во включенных процессов (аккаунтов, пауков)
        count_groups_spiders = int(os.getenv('COUNT_GROUPS_SPIDERS'))

        token = os.getenv('ACCOUNT_TOKENS').split(',')[number_of_account-1]  # рабочий токен

        # with open('config.json', 'a') as config_file:
        #     config_file.write(token + '\n')

        groups_list = self.get_list_groups(count_groups, count_process, number_of_groups, count_groups_spiders)  # итоговый список

        url_groups = f'https://api.vk.com/method/groups.getById?access_token={token}&v=5.154&group_ids=1&fields=can_see_all_posts,members_count'

        yield scrapy.Request(
            url=url_groups,
            callback=self.parse,
            meta={'groups_list': groups_list, 'token': token},
        )

    def parse(self, response: HtmlResponse):
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
        try:
            result_groups_data = sum(groups_data['response'], [])
            yield ParseSocialMediaItem(type='group', data=result_groups_data)
        except KeyError:
            self.logger.debug(f'Got wall_data: {groups_data}')
