from dotenv import load_dotenv

load_dotenv()

from service import request_check_tokens, file_parse_accounts, start_project
import os
import multiprocessing

from parse_social_media.spiders.vk_parse_groups import VkParseGroupSpider

from parse_social_media.spiders.vk_parse_posts import VkParsePostsSpider

from parse_social_media.settings import PATH_BASE


if __name__ == "__main__":

    result_accounts = file_parse_accounts(f'{PATH_BASE}/accounts_data.txt', 2)
    if os.getenv("CHECK_ACCOUNTS"):
        print('Проверка токенов...')
        result_accounts = request_check_tokens(result_accounts, 1)
        list_result_accounts = len(result_accounts.split(','))
        print(f'Проверка токенов завершена. Рабочих токенов {list_result_accounts} шт.')

    os.environ['ACCOUNT_TOKENS'] = result_accounts

    # Классы пауков
    spiders_to_run = (VkParseGroupSpider, VkParsePostsSpider)

    # запущенные процессы
    processes = []

    count_process = int(os.getenv('COUNT_PROCESS'))

    count_groups_spiders_in_process = int(os.getenv('COUNT_GROUPS_SPIDERS'))

    # берем все аккаунты и делим их на кол-во процессов == получаем группу аккаунтов для каждого процесса

    # запуск процессов (пауков)
    for num_process in range(0, count_process):
        print(f"Запуск паука {spiders_to_run}...")
        process = multiprocessing.Process(target=start_project, args=(spiders_to_run, num_process, count_groups_spiders_in_process, ))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    print("Все пауки закончили работу.")
