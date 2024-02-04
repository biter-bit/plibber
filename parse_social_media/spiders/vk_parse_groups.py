import scrapy
from scrapy.http import HtmlResponse
import os
import json
from parse_social_media.items import ParseSocialMediaItem
import math
from parse_social_media.custom_exception import Error29Exception, Error13Exception, Error6Exception
from parse_social_media.service import error
from datetime import datetime, timedelta


def get_script_vk_parse_groups(groups_id_list_vk_parse):
    """Создает скрипт для запроса execute к vk api"""
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


def get_list_groups(count_groups, count_process, number_of_group, count_groups_spiders):
    """Возвращает список групп для указанного номера паука"""
    # индекс последнего элемента
    ending_position = count_groups // count_process // count_groups_spiders * number_of_group + 1
    # индекс первого элемента
    starting_position = ending_position - count_groups // count_process // count_groups_spiders
    groups_list = list(range(starting_position, ending_position))
    return groups_list


class VkParseGroupSpider(scrapy.Spider):
    name = "vk_parse_group_1"

    def __init__(self, number_of_account=None, number_of_groups=None, name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        # рабочий токен
        self.token = os.getenv('ACCOUNT_TOKENS').split(',')[number_of_account - 1]
        # итоговый список
        self.groups_list = list(range(int(os.getenv('START_IDX_GROUP')), int(os.getenv('END_IDX_GROUP'))))
        self.groups_parse = [None]
        # кол-во групп, которые нужно обработать
        self.count_groups = int(os.getenv('END_IDX_GROUP')) - int(os.getenv('START_IDX_GROUP'))
        # кол-во включенных процессов (аккаунтов, пауков)
        self.count_process = int(os.getenv('COUNT_PROCESS'))
        # кол-во пауков на каждый процесс
        self.count_groups_spiders = int(os.getenv('COUNT_GROUPS_SPIDERS'))
        self.error = 'done'
        self.list_errors = []

    def start_requests(self):
        url_groups = (f'https://api.vk.com/method/groups.getById?'
                      f'access_token={self.token}&v=5.154&group_ids=1&fields=can_see_all_posts,members_count')
        yield scrapy.Request(url=url_groups, callback=self.parse)

    def parse(self, response: HtmlResponse):
        groups_data = response.json()
        try:
            # вызываем raise если есть ошибки 6, 13, 29
            error(groups_data)

            # кол-во всех запросов внутри всех execute (int)
            number_of_requests = math.ceil(len(self.groups_list) / 350)
            # кол-во запросов execute (int)
            number_total_requests = math.ceil(number_of_requests / 25)

            #  проверка деления на ноль
            if number_total_requests != 0:
                # кол-во обрабатываемых групп за один запрос execute
                number_iter_groups = len(self.groups_list) // number_total_requests
            else:
                number_iter_groups = 0

            # получение групп
            for i in range(0, number_total_requests):
                # список групп для одного из execute
                groups_parse = self.groups_list[i * number_iter_groups:i * number_iter_groups + number_iter_groups]
                vk_script = get_script_vk_parse_groups(groups_parse)
                url = f'https://api.vk.com/method/execute'
                yield scrapy.FormRequest(
                    url=url,
                    method='POST',
                    callback=self.groups_preparetion,
                    formdata={'access_token': self.token, 'code': vk_script, 'v': "5.154"},
                    meta={'groups_parse': groups_parse}
                )

        except Error6Exception:
            self.error = 6
            self.list_errors.append({
                "id_group_start": self.groups_list[0],
                "id_group_finish": self.groups_parse[-1] + 1 if self.groups_parse else None,
                "id_group_start_execute": self.groups_parse[0],
                "id_group_finish_execute": self.groups_parse[-1] + 1 if self.groups_parse else None,
                "error": self.error
            })

        except Error13Exception:
            self.error = 13
            self.list_errors.append({
                "id_group_start": self.groups_list[0],
                "id_group_finish": self.groups_parse[-1] + 1 if self.groups_parse else None,
                "id_group_start_execute": self.groups_parse[0],
                "id_group_finish_execute": self.groups_parse[-1] + 1 if self.groups_parse else None,
                "error": self.error
            })

        except Error29Exception:
            self.error = 29
            self.list_errors.append({
                "id_group_start": self.groups_list[0],
                "id_group_finish": self.groups_parse[-1] + 1 if self.groups_parse else None,
                "id_group_start_execute": self.groups_parse[0],
                "id_group_finish_execute": self.groups_parse[-1] + 1 if self.groups_parse else None,
                "error": self.error
            })

    def groups_preparetion(self, response: HtmlResponse):
        groups_data = response.json()
        self.groups_parse = response.meta["groups_parse"]

        try:
            # вызываем raise если есть ошибки 6, 13, 29
            error(groups_data)

            result_groups_data = sum(groups_data['response'], [])
            yield ParseSocialMediaItem(type='group', data=result_groups_data)

        except Error6Exception:
            self.error = 6
            self.list_errors.append({
                "id_group_start": self.groups_list[0],
                "id_group_finish": self.groups_parse[-1] + 1 if self.groups_parse else None,
                "id_group_start_execute": self.groups_parse[0],
                "id_group_finish_execute": self.groups_parse[-1] + 1 if self.groups_parse else None,
                "error": self.error
            })

        except Error13Exception:
            self.error = 13
            self.list_errors.append({
                "id_group_start": self.groups_list[0],
                "id_group_finish": self.groups_parse[-1] + 1 if self.groups_parse else None,
                "id_group_start_execute": self.groups_parse[0],
                "id_group_finish_execute": self.groups_parse[-1] + 1 if self.groups_parse else None,
                "error": self.error
            })

        except Error29Exception:
            self.error = 29
            self.list_errors.append({
                "id_group_start": self.groups_list[0],
                "id_group_finish": self.groups_parse[-1] + 1 if self.groups_parse else None,
                "id_group_start_execute": self.groups_parse[0],
                "id_group_finish_execute": self.groups_parse[-1] + 1 if self.groups_parse else None,
                "error": self.error
            })

    def close(self, reason):
        # получение текущей даты и времени
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime("%d/%m/%Y %H:%M:%S")

        # получение даты и времени через 24 часа
        new_datetime = current_datetime + timedelta(hours=24)
        formatted_new_datetime = new_datetime.strftime("%d/%m/%Y %H:%M:%S")

        # if reason == "closespider_pagecount":
        #     self.list_errors.append({
        #         "id_group_start": self.groups_list[0],
        #         "id_group_finish": self.groups_list[-1],
        #         "id_group_start_execute": self.groups_parse[0],
        #         "id_group_finish_execute": self.groups_parse[-1],
        #         "error": self.error
        #     })

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
        existing_file_path = f'data/error_groups.json'
        try:
            # Прочитать данные из существующего файла
            with open(existing_file_path, 'r') as json_file:
                existing_data = json.load(json_file)
            os.remove(existing_file_path)
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
