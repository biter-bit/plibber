from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from dotenv import load_dotenv
import os
import requests

from parse_social_media.spiders.vk_parse import VkParseSpider
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


def request_check_tokens(tokens):
    list_work_accounts = []
    for token in tokens:
        try:
            # response = requests.get('https://api.vk.com/method/users.get?user_ids=1&v=5.154&access_token=' + token)
            response = requests.get('https://api.vk.com/method/groups.getById?group_ids=1&v=5.154&access_token=' + token)
            if 'error' not in response.text:
                list_work_accounts.append(token)
        except Exception as e:
            print(f"Error processing token {token}: {e}")
    str_work_accounts = ','.join(list_work_accounts)
    return str_work_accounts


if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    result_accounts = file_parse_accounts('../accounts_data.txt', 2)
    if settings.CHECK_ACCOUNTS:
        print('Проверка токенов...')
        result_accounts = request_check_tokens(result_accounts)
        print('Проверка токенов завершена')
    os.environ['VK_ACCESS_TOKEN'] = result_accounts
    load_dotenv()

    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(VkParseSpider)

    process.start()
