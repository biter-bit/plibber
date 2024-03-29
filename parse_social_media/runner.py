from dotenv import load_dotenv

load_dotenv()

from service import main_checker_accounts, file_parse_accounts, main_checker_proxy, run
import os
from parse_social_media.spiders.vk_parse_groups import VkParseGroupSpider
from parse_social_media.spiders.vk_parse_posts import VkParsePostsSpider
from parse_social_media.spiders.vk_parse_update import VkParseUpdateSpider
from parse_social_media.settings import PATH_BASE

if __name__ == "__main__":

    # получение всех аккаунтов/прокси и проверка их на работоспособность
    proxys = main_checker_proxy(
        f'{PATH_BASE}/data/proxys.txt',
        f'{PATH_BASE}/data/work_proxys.txt',
        f'{PATH_BASE}/data/not_work_proxys.txt',
        True
    )
    accounts = main_checker_accounts(
        f'{PATH_BASE}/data/accounts_data.txt',
        proxys,
        f'{PATH_BASE}/data/work_accounts.txt',
        f'{PATH_BASE}/data/not_work_accounts.txt',
        True
    )

    # Классы пауков
    spiders_to_run = (VkParseGroupSpider, VkParsePostsSpider, VkParseUpdateSpider)

    count_process = int(os.getenv('COUNT_PROCESS'))  # кол-во процессов
    count_groups_spiders_in_process = int(os.getenv('COUNT_GROUPS_SPIDERS'))  # кол-во групп пауков (по 2)
    count_accounts_tokens = len(accounts.split(','))  # кол-во аккаунтов
    count_proxys = len(proxys.split(','))  # кол-во прокси
    parse_group_value = int(os.getenv('GROUP_PARSE_START'))  # вкл/выкл парсинг групп
    parse_posts_value = int(os.getenv('POSTS_PARSE_START'))  # вкл/выкл парсинг постов
    parse_update_value = int(os.getenv('UPDATE_PARSE_START'))  # вкл/выкл обновление постов

    run(
        count_proxys,
        count_accounts_tokens,
        count_groups_spiders_in_process,
        count_process,
        spiders_to_run,
        parse_group_value,
        parse_posts_value,
        parse_update_value
    )
