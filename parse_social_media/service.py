import requests
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess, Crawler, CrawlerRunner


def start_project(spider):
    process = CrawlerProcess(settings=get_project_settings())
    process.crawl(spider[0])
    process.crawl(spider[1])
    process.start()


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


# def file_parse_proxys(file_path):
#     """Парсит файл с прокси формата - ip:port:login:password\n"""
#     with open(file_path, 'r') as file:
#         list_proxys = []
#         for proxy in file:
#             list_proxys.append(proxy.strip())
#         result_accounts = ','.join(list_proxys)
#
#     return result_accounts


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
