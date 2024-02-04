import socket
import threading
import os
import requests
from requests.exceptions import RequestException


def check_proxy(proxy_full, work_proxy, not_work_proxy):
    try:
        proxy_format = {
            'http': proxy_full,
        }
        response = requests.get(url='https://httpbin.org/', proxies=proxy_format, timeout=5)
        response.raise_for_status()

        # print(f"Proxy {proxy_full} is working with credentials")
        work_proxy.append(proxy_full)
    except RequestException as e:
        # print(f"Proxy {proxy_full} is not working with credentials")
        not_work_proxy.append(proxy_full)


def save_in_files_proxys(file_work_proxy, file_not_work_proxy, work_proxy, not_work_proxy):
    for file_ in (file_work_proxy, file_not_work_proxy):
        try:
            os.remove(file_)
            # print(f"File '{file_}' deleted.")
        except FileNotFoundError:
            pass
            # print(f"File '{file_}' not found.")
        with open(file_, "w") as file:
            if file_ == file_work_proxy:
                for proxy in work_proxy:
                    file.write(f'{proxy}\n')
            elif file_ == file_not_work_proxy:
                for proxy in not_work_proxy:
                    file.write(f'{proxy}\n')
    return 'Ok'


def main_checker_proxy(file_read, file_work_proxy, file_not_work_proxy, return_str=False):
    print("Проверка прокси...")
    work_proxy = []
    not_work_proxy = []
    threads = []
    with open(file_read, 'r') as file:
        for proxy_line in file:
            proxy_full = proxy_line.strip()
            thread = threading.Thread(target=check_proxy,
                                      args=(proxy_full, work_proxy, not_work_proxy))
            thread.start()
            threads.append(thread)

    for thread in threads:
        thread.join()

    save_in_files_proxys(file_work_proxy, file_not_work_proxy, work_proxy, not_work_proxy)
    str_proxys = ','.join(work_proxy)
    os.environ['PROXY_TOKENS'] = str_proxys
    print(f'Проверка прокси завершена. Рабочих прокси {len(work_proxy)} шт.\n')
    return str_proxys if return_str else work_proxy
