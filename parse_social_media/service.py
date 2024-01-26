import requests
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from typing import List, Union, Tuple
from requests.exceptions import ProxyError
import os
import multiprocessing
from custom_exception import Error29Exception, Error13Exception, Error6Exception


def error(response):
    """Проверяет ошибки вк и вызывает exception если они есть"""
    if 'error' in response and 'error_code' in response['error']:
        if response['error']['error_code'] == 29:
            raise Error29Exception("Error 29. Rate limit reached")
        if response['error']['error_code'] == 13:
            raise Error13Exception("Error 13. Response size is too big.")
        if response['error']['error_code'] == 6:
            raise Error6Exception("Error 6. Too many requests per second.")


def checker(accounts: list, proxys: list) -> tuple[list[str] | str, list[str] | str]:
    """Добавляет работоспособные аккаунты и прокси в переменные окружения"""
    if os.getenv("CHECK"):
        print('Проверка токенов...')
        result_accounts = request_check_tokens(accounts, True)
        list_result_accounts = len(result_accounts.split(','))
        os.environ['ACCOUNT_TOKENS'] = result_accounts
        print(f'Проверка токенов завершена. Рабочих токенов {list_result_accounts} шт.\n')
        print("Проверка прокси...")
        result_proxys = request_check_proxys(proxys, True)
        list_result_proxys = len(result_proxys.split(','))
        os.environ['PROXY_TOKENS'] = result_proxys
        print(f'Проверка прокси завершена. Рабочих прокси {list_result_proxys} шт.\n')
    else:
        result_proxys = accounts
        result_accounts = proxys

    return result_accounts, result_proxys


def file_parse_accounts(file_path: str, return_str: bool = False) -> Union[List[str], str]:
    """
    Возвращает список или строку токенов аккаунта vk из файла. Формат файла должен быть - login:password:token\n.

        Параметры:
            file_path (str): путь к файлу с информацией о прокси
            return_str (bool): тип возвращаемого контента (по умолчанию False).

        Возвращает:
            Union[List[str], str, None]: ваша ожидаемая строка, список строк или None
    """
    with open(file_path, 'r') as file:
        list_accounts = []
        for account in file:
            token = account.split(':')[2].strip()
            list_accounts.append(token)
        str_accounts = ','.join(list_accounts)
    return str_accounts if return_str else list_accounts


def file_parse_proxy(file_path: str, return_str: bool = False) -> Union[List[str], str]:
    """
    Возвращает список или строку прокси из файла. Формат файла должен быть - login:password@ip:port\n.

        Параметры:
            file_path (str): путь к файлу с информацией о прокси
            return_str (bool): тип возвращаемого контента (по умолчанию False).

        Возвращает:
            Union[List[str], str, None]: ваша ожидаемая строка, список строк или None
    """
    with open(file_path, 'r') as file:
        list_proxys = []
        for proxy_line in file:
            list_proxys.append(proxy_line.strip())
        str_proxys = ','.join(list_proxys)
    return str_proxys if return_str else list_proxys


def request_check_tokens(tokens: List[str], return_str: bool = False) -> Union[List[str], str]:
    """Получает список токенов vk и проверяет их на работоспособность"""
    list_work_accounts = []
    for token in tokens:
        try:
            response = requests.get('https://api.vk.com/method/groups.getById?group_ids=1&v=5.154&access_token=' + token)
            if 'error' not in response.text:
                list_work_accounts.append(token)
        except Exception as e:
            print(f"Error processing token {token}: {e}")
    str_work_accounts = ','.join(list_work_accounts)
    return str_work_accounts if return_str else list_work_accounts


def request_check_proxys(proxys: List[str], return_str: bool = False) -> Union[List[str], str]:
    """Получает список прокси и проверяет их на работоспособность"""
    list_work_proxys = []
    for proxy in proxys:
        try:
            proxy_format = {
                'http': proxy,
                'https': proxy
            }
            response = requests.get('https://google.ru', proxy_format)
            response.raise_for_status()
            list_work_proxys.append(proxy)
        except ProxyError as e:
            print(f"Error processing proxy {proxy}: {e}")
    str_work_accounts = ','.join(list_work_proxys)
    return str_work_accounts if return_str else list_work_proxys


def run(
        count_proxys,
        count_accounts,
        count_spiders,
        count_process,
        spiders_tuple,
        parse_group_value,
        parse_posts_value,
        parse_update_value):
    # список запущенных процессы
    processes = []

    if count_proxys < count_accounts:
        raise Exception(f'Недостаточно прокси для всех аккаунтов. Минимум 1 прокси на 1 аккаунт')

    if count_process * (count_spiders*(parse_update_value+parse_group_value+parse_posts_value)) > count_accounts:
        raise Exception(f'Недостаточно рабочих аккаунтов для данной настройки')

    if count_process * count_spiders > int(os.getenv('COUNT_GROUPS')):
        raise Exception(f'Слишком много пауков для данного кол-ва групп. Нужно использовать максимум 1 паука на 1 группу.')

    if parse_group_value and parse_posts_value and parse_update_value:
        raise Exception(f'Нельзя включать сразу обновление и парсинг постов.')

    # запуск процессов (пауков)
    for num_process in range(0, count_process):
        print(f"Запуск паука {spiders_tuple}...")
        process = multiprocessing.Process(target=start_project,
                                          args=(
                                              spiders_tuple,
                                              num_process,
                                              count_spiders,
                                              parse_group_value,
                                              parse_posts_value,
                                              parse_update_value
                                          ))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    print("Все пауки закончили работу.")


def start_project(spiders, num_process, count_groups_spiders, parse_group_value, parse_posts_value, parse_update_value):
    """Запускает пауков"""
    process = CrawlerProcess(settings=get_project_settings())
    spider_group = spiders[0]
    spider_post = spiders[1]
    spider_update = spiders[2]

    for i in range(num_process*count_groups_spiders, num_process*count_groups_spiders+count_groups_spiders):
        custom_settings_group = {
            'CONCURRENT_REQUESTS': 3,
            'DOWNLOAD_DELAY': 1.5,
            'ROTATING_PROXY_LIST': [os.getenv('PROXY_TOKENS').split(',')[i]],
            # 'CLOSESPIDER_PAGECOUNT': 1
        }

        spider_group.custom_settings = custom_settings_group
        spider_group.settings = get_project_settings().copy()
        spider_group.settings.update(custom_settings_group)

        custom_settings_post = {
            'CONCURRENT_REQUESTS': 3,
            'DOWNLOAD_DELAY': 1.5,
            'ROTATING_PROXY_LIST': [os.getenv('PROXY_TOKENS').split(',')[i+1]],
            'CLOSESPIDER_PAGECOUNT': os.getenv('CLOSESPIDER_POST')
        }

        spider_post.custom_settings = custom_settings_post
        spider_post.settings = get_project_settings().copy()
        spider_post.settings.update(custom_settings_post)

        custom_settings_update = {
            'CONCURRENT_REQUESTS': 3,
            'DOWNLOAD_DELAY': 1.5,
            'ROTATING_PROXY_LIST': [os.getenv('PROXY_TOKENS').split(',')[i+1]],
            'CLOSESPIDER_PAGECOUNT': os.getenv('CLOSESPIDER_POST')
        }

        spider_update.custom_settings = custom_settings_update
        spider_update.settings = get_project_settings().copy()
        spider_update.settings.update(custom_settings_update)

        if parse_group_value:
            process.crawl(spider_group, number_of_account=2*i+1, number_of_groups=i+1, name=f'vk_parse_group_{i+1}')
        if parse_posts_value:
            process.crawl(spider_post, number_of_account=2*i+2, number_of_groups=i+1, name=f'vk_parse_posts_{i+2}')
        if parse_update_value:
            process.crawl(spider_update, number_of_account=i+1, number_of_groups=i+1, name=f'vk_parse_posts_{i+2}')

    process.start()
