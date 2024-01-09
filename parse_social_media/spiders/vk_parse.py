import scrapy
from dotenv import load_dotenv
import os
import random

load_dotenv()


class VkParseSpider(scrapy.Spider):
    name = "vk_parse"
    start_urls = ['https://vk.com/']

    def calculate_account_range(self, count_groups, count_accounts, idx):
        range_id_end = count_groups // count_accounts * idx
        range_id_start = range_id_end - (count_groups // count_accounts)
        result_string = ','.join(map(str, range(range_id_start + 1, range_id_end + 1)))
        yield result_string

    def start_requests(self):
        count_groups = int(os.getenv("COUNT_GROUPS"))
        count_accounts = int(os.getenv("COUNT_ACCOUNTS"))
        tokens = os.getenv(f"VK_ACCESS_TOKEN").split(',')
        proxys = os.getenv(f"PROXY_ADDRESS").split(',')

        if len(tokens) != count_accounts:
            os.environ["COUNT_ACCOUNTS"] = str(len(tokens))
            count_accounts = len(tokens)

        len_proxys_list = len(proxys)

        for idx in range(1, count_accounts + 1):
            if len_proxys_list < idx:
                proxy = random.choice(proxys)
            else:
                proxy = proxys[idx - 1]
            token = tokens[idx-1]

            result_string = self.calculate_account_range(count_groups, count_accounts, idx)

            if token and proxy:
                yield scrapy.Request(
                    url=f'https://api.vk.com/method/groups.getById?access_token={token}&v=5.154&group_ids={idx}&fields=can_see_all_posts,members_count',
                    callback=self.parse,
                    meta={'proxy': proxy, 'range_id': result_string, 'token': token}
                )

    def parse(self, response):
        range_id = response.meta['range_id']
        token = response.meta['token']
        link = f'https://api.vk.com/method/groups.getById?access_token={token}&v=5.154&group_ids={range_id}&fields=can_see_all_posts,members_count'
        yield response.follow(link, callback=self.func)
        print(response.url)

    def func(self):
        pass

