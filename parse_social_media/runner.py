from dotenv import load_dotenv

load_dotenv()

from service import request_check_tokens, file_parse_accounts, start_project
import os
import multiprocessing

from parse_social_media.spiders.vk_parse_groups import VkParseGroupSpider1
from parse_social_media.spiders.vk_parse_groups_2 import VkParseGroupSpider2
from parse_social_media.spiders.vk_parse_groups_3 import VkParseGroupSpider3
from parse_social_media.spiders.vk_parse_groups_4 import VkParseGroupSpider4
from parse_social_media.spiders.vk_parse_groups_5 import VkParseGroupSpider5
from parse_social_media.spiders.vk_parse_groups_6 import VkParseGroupSpider6
from parse_social_media.spiders.vk_parse_groups_7 import VkParseGroupSpider7
from parse_social_media.spiders.vk_parse_groups_8 import VkParseGroupSpider8
from parse_social_media.spiders.vk_parse_groups_9 import VkParseGroupSpider9
from parse_social_media.spiders.vk_parse_groups_10 import VkParseGroupSpider10

from parse_social_media.spiders.vk_parse_posts import VkParsePostsSpider1
from parse_social_media.spiders.vk_parse_posts_2 import VkParsePostsSpider2
from parse_social_media.spiders.vk_parse_posts_3 import VkParsePostsSpider3
from parse_social_media.spiders.vk_parse_posts_4 import VkParsePostsSpider4
from parse_social_media.spiders.vk_parse_posts_5 import VkParsePostsSpider5
from parse_social_media.spiders.vk_parse_posts_6 import VkParsePostsSpider6
from parse_social_media.spiders.vk_parse_posts_7 import VkParsePostsSpider7
from parse_social_media.spiders.vk_parse_posts_8 import VkParsePostsSpider8
from parse_social_media.spiders.vk_parse_posts_9 import VkParsePostsSpider9
from parse_social_media.spiders.vk_parse_posts_10 import VkParsePostsSpider10

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
    spiders_to_run = [
        (VkParseGroupSpider1, VkParsePostsSpider1),
        (VkParseGroupSpider2, VkParsePostsSpider2),
        (VkParseGroupSpider3, VkParsePostsSpider3),
        (VkParseGroupSpider4, VkParsePostsSpider4),
        (VkParseGroupSpider5, VkParsePostsSpider5),
        (VkParseGroupSpider6, VkParsePostsSpider6),
        (VkParseGroupSpider7, VkParsePostsSpider7),
        (VkParseGroupSpider8, VkParsePostsSpider8),
        (VkParseGroupSpider9, VkParsePostsSpider9),
        (VkParseGroupSpider10, VkParsePostsSpider10),
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
