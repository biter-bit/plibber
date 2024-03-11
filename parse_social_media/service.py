import random

import requests
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from typing import List, Union, Tuple
from requests.exceptions import ProxyError
import os
import multiprocessing
from custom_exception import Error29Exception, Error13Exception, Error6Exception
import urllib
import socket
import threading
from requests.exceptions import RequestException
from parse_social_media.settings import PATH_BASE


def error(response):
    """Проверяет ошибки вк и вызывает exception если они есть"""
    if 'error' in response and 'error_code' in response['error']:
        if response['error']['error_code'] == 29:
            raise Error29Exception("Error 29. Rate limit reached")
        if response['error']['error_code'] == 13:
            raise Error13Exception("Error 13. Response size is too big.")
        if response['error']['error_code'] == 6:
            raise Error6Exception("Error 6. Too many requests per second.")


def save_in_files(file_work, file_not_work, working, not_working):
    """Сохраняет рабочие и не рабочие прокси/аккаунты в файлы"""
    for file_ in (file_work, file_not_work):
        try:
            os.remove(file_)
            # print(f"File '{file_}' deleted.")
        except FileNotFoundError:
            pass
            # print(f"File '{file_}' not found.")
        with open(file_, "w") as file:
            if file_ == file_work:
                for i in working:
                    file.write(f'{i}\n')
            elif file_ == file_not_work:
                for i in not_working:
                    file.write(f'{i}\n')
    return 'Ok'


def check_proxy(proxy_full, work_proxy, not_work_proxy):
    """Проверяет работоспособость одного прокси"""
    try:
        proxy_format = {
            'http': proxy_full,
            'https': proxy_full
        }
        response = requests.get(url='https://api64.ipify.org?format=json', proxies=proxy_format, timeout=5)
        response.raise_for_status()

        # print(f"Proxy {proxy_full} is working with credentials")
        work_proxy.append(proxy_full[7:])
    except RequestException as e:
        # print(f"Proxy {proxy_full} is not working with credentials")
        not_work_proxy.append(proxy_full[7:])


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


def main_checker_proxy(file_read, file_work_proxy, file_not_work_proxy, return_str=False):
    """Проверяет работоспособность прокси"""
    list_proxies = file_parse_proxy(file_read)
    if os.getenv("CHECK"):
        print("Проверка прокси...")
        work_proxy = []
        not_work_proxy = []
        threads = []
        for proxy_line in list_proxies:
            proxy_full = f'http://{proxy_line}'
            thread = threading.Thread(target=check_proxy,
                                      args=(proxy_full, work_proxy, not_work_proxy))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        save_in_files(file_work_proxy, file_not_work_proxy, work_proxy, not_work_proxy)
        str_proxys = ','.join(work_proxy)
        os.environ['PROXY_TOKENS'] = str_proxys
        print(f'Проверка прокси завершена. Рабочих прокси {len(work_proxy)} шт.\n')
        return str_proxys if return_str else work_proxy
    else:
        print("Прокси не проверены, так как настройка выключена")
        str_proxys = ','.join(list_proxies)
        return str_proxys if return_str else list_proxies


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


def check_account(proxy_full, token, work_account, not_work_account):
    """Проверяет работоспособость одного аккаунта"""
    try:
        proxy_format = {
            'http': proxy_full,
            'https': proxy_full
        }
        response = requests.get(
            url='https://api.vk.com/method/groups.getById?group_ids=1&v=5.154&access_token=' + token,
            proxies=proxy_format,
            timeout=5
        )
        if 'error' not in response.text:
            work_account.append(token)
        response.raise_for_status()
    except RequestException as e:
        not_work_account.append(token)
        print(f"Error processing token {token}: {e}")
    except Exception as e:
        not_work_account.append(token)
        print(f"Error processing token {token}: {e}")


def main_checker_accounts(accounts_path: str, proxies: str, name_file_work, name_file_not_work, return_str=False) -> list[str] | str | list:
    """Проверяет работоспособность аккаунтов (токенов)"""
    accounts_list = file_parse_accounts(accounts_path)
    if os.getenv("CHECK"):
        print('Проверка токенов...')
        list_work_accounts = []
        list_not_work_accounts = []
        threads = []
        for account in accounts_list:
            proxies_list = proxies.split(',')
            proxy_full = f'http://{random.choice(proxies_list)}'
            thread = threading.Thread(target=check_account,
                                      args=(proxy_full, account, list_work_accounts, list_not_work_accounts))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        save_in_files(name_file_work, name_file_not_work, list_work_accounts, list_not_work_accounts)
        str_accounts = ','.join(list_work_accounts)
        os.environ['ACCOUNT_TOKENS'] = str_accounts
        print(f'Проверка токенов завершена. Рабочих токенов {len(list_work_accounts)} шт.\n')
        return str_accounts if return_str else list_work_accounts
    else:
        print("Аккаунты не проверены, так как настройка выключена")
        str_proxys = ','.join(accounts_list)
        return str_proxys if return_str else accounts_list


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

    if count_proxys < count_accounts and count_proxys < count_process * count_spiders:
        raise Exception(f'Недостаточно прокси для всех аккаунтов. Минимум 1 прокси на 1 аккаунт')

    if count_process * (count_spiders*(parse_update_value+parse_group_value+parse_posts_value)) > count_accounts:
        raise Exception(f'Недостаточно рабочих аккаунтов для данной настройки')

    if count_process * count_spiders > int(os.getenv('END_IDX_GROUP'))-int(os.getenv('START_IDX_GROUP')):
        raise Exception(f'Слишком много пауков для данного кол-ва групп. Нужно использовать максимум 1 паука на 1 '
                        f'группу.')

    if parse_update_value and (parse_posts_value or parse_group_value):
        raise Exception(f'Нельзя включать сразу обновление и парсинг постов/групп.')

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
            'ROTATING_PROXY_LIST': [
                os.getenv('PROXY_TOKENS').split(',')[i+1]
                if parse_group_value and parse_posts_value
                else os.getenv('PROXY_TOKENS').split(',')[i]],
            'CLOSESPIDER_PAGECOUNT': os.getenv('CLOSESPIDER_POST')
        }

        spider_post.custom_settings = custom_settings_post
        spider_post.settings = get_project_settings().copy()
        spider_post.settings.update(custom_settings_post)

        custom_settings_update = {
            'CONCURRENT_REQUESTS': 3,
            'DOWNLOAD_DELAY': 1.5,
            'ROTATING_PROXY_LIST': [os.getenv('PROXY_TOKENS').split(',')[i]],
            'CLOSESPIDER_PAGECOUNT': os.getenv('CLOSESPIDER_POST')
        }

        spider_update.custom_settings = custom_settings_update
        spider_update.settings = get_project_settings().copy()
        spider_update.settings.update(custom_settings_update)

        if parse_group_value and parse_posts_value:
            process.crawl(spider_post, number_of_account=2*i+2, number_of_groups=i+1, name=f'vk_parse_posts_{i+1}')
            process.crawl(spider_group, number_of_account=2*i+1, number_of_groups=i+1, name=f'vk_parse_group_{i+1}')
        if parse_group_value and not parse_posts_value:
            process.crawl(spider_group, number_of_account=i+1, number_of_groups=i+1, name=f'vk_parse_group_{i+1}')
        if parse_posts_value and not parse_group_value:
            process.crawl(spider_post, number_of_account=i+1, number_of_groups=i+1, name=f'vk_parse_posts_{i + 1}')
        if parse_update_value:
            process.crawl(spider_update, number_of_account=i+1, number_of_groups=i+1, name=f'vk_parse_update_{i+1}')

    process.start()
