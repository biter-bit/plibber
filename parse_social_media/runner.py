from dotenv import load_dotenv

load_dotenv()

from scrapy.crawler import CrawlerProcess, Crawler, CrawlerRunner
from scrapy.settings import Settings
import os
import requests
import multiprocessing
import time
from scrapy.utils.project import get_project_settings

from parse_social_media.spiders.vk_parse import VkParseSpider
from parse_social_media.spiders.vk_parse2 import VkParse2Spider
from parse_social_media.spiders.vk_parse3 import VkParse3Spider
from parse_social_media.spiders.vk_parse4 import VkParse4Spider
from parse_social_media.spiders.vk_parse5 import VkParse5Spider
from parse_social_media.spiders.vk_parse6 import VkParse6Spider
from parse_social_media.spiders.vk_parse7 import VkParse7Spider
from parse_social_media.spiders.vk_parse8 import VkParse8Spider
from parse_social_media.spiders.vk_parse9 import VkParse9Spider
from parse_social_media.spiders.vk_parse10 import VkParse10Spider

from parse_social_media.settings import PATH_BASE
from parse_social_media import settings


def file_parse_accounts(file_path, type_content):
    """Парсит файл с аккаунтами формата - login:password:token\n"""
    with open(file_path, 'r') as file:
        list_accounts = []
        for account in file:
            list_data_accounts = account.split(':')
            token = list_data_accounts[2]
            list_accounts.append(token.strip())

        if type_content == 1:
            result_accounts = ','.join(list_accounts)
        elif type_content == 2:
            result_accounts = list_accounts

    return result_accounts


# def parse_proxy_v2(file_path):
#     with open(file_path, 'r') as file:
#         list_accounts = []
#         for account in file:
#             list_data_accounts = account.split('@')
#             token = list_data_accounts[1].strip() + '@' + list_data_accounts[0] + '\n'
#             list_accounts.append(token)
#             # yield scrapy.http.FormRequest(
#             #     url=f'https://api.vk.com/method/users.get',
#             #     user_ids="1",
#             #     callback=check_token
#             # )
#             # print()
#         result_accounts = ''.join(list_accounts)
#     with open(file_path, 'w') as file:
#         file.write(result_accounts)
#
#     return result_accounts


# def file_parse_proxys(file_path):
#     """Парсит файл с прокси формата - ip:port:login:password\n"""
#     with open(file_path, 'r') as file:
#         list_proxys = []
#         for proxy in file:
#             list_proxys.append(proxy.strip())
#         result_accounts = ','.join(list_proxys)
#
#     return result_accounts


def request_check_tokens(tokens, mode):
    list_work_accounts = []
    for token in tokens:
        try:
            response = requests.get('https://api.vk.com/method/groups.getById?group_ids=1&v=5.154&access_token=' + token)
            if 'error' not in response.text:
                list_work_accounts.append(token)
        except Exception as e:
            print(f"Error processing token {token}: {e}")
    work_accounts = list_work_accounts
    if mode == 1:
        work_accounts = ','.join(list_work_accounts)
    return work_accounts


def start_project(spider):
    process = CrawlerProcess(settings=get_project_settings())
    process.crawl(spider)
    process.start()


if __name__ == "__main__":

    result_accounts = file_parse_accounts(f'{PATH_BASE}/accounts_data.txt', 2)
    if os.getenv("CHECK_ACCOUNTS"):
        print('Проверка токенов...')
        result_accounts = request_check_tokens(result_accounts, 1)
        list_result_accounts = len(result_accounts.split(','))
        print(f'Проверка токенов завершена. Рабочих токенов {list_result_accounts} шт.')

    os.environ['ACCOUNT_TOKENS'] = result_accounts

    # Название проекта
    project_name = "parse_social_media"

    # Классы пауков
    spiders_to_run = [
        VkParseSpider,
        VkParse2Spider,
        VkParse3Spider,
        VkParse4Spider,
        VkParse5Spider,
        VkParse6Spider,
        VkParse7Spider,
        VkParse8Spider,
        VkParse9Spider,
        VkParse10Spider
    ]

    # запущенные процессы
    processes = []

    count_spiders = int(os.getenv('COUNT_SPIDERS'))

    # запуск процессов (пауков)
    for idx in range(0, count_spiders):
        print(f"Запуск паука {spiders_to_run[idx]}...")
        process = multiprocessing.Process(target=start_project, args=(spiders_to_run[idx],))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    print("Все пауки закончили работу.")
