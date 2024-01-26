import logging

from scrapy import signals
import os
from datetime import datetime, timedelta
import json


class MyExtension:
    def __init__(self, crawler):
        self.crawler = crawler
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        extension = cls(crawler)
        crawler.signals.connect(extension.spider_closed, signal=signals.spider_closed)
        return extension

    def spider_closed(self, spider, reason):
        try:
            token = os.getenv('ACCOUNT_TOKENS').split(',')[spider.number_of_account-1]

            current_datetime = datetime.now()
            formatted_date = current_datetime.strftime("%d/%m/%Y %H:%M:%S")

            new_datetime = current_datetime + timedelta(hours=24)
            formatted_new_datetime = new_datetime.strftime("%d/%m/%Y %H:%M:%S")

            date_to_save = {
                token: {
                    "token": token,
                    "date_finish": formatted_date,
                    "reboot_date": formatted_new_datetime,
                    "groups_list": spider.groups_list,
                }
            }

            existing_file_path = f'logs/token_finish_error_{spider.error}.json'

            try:
                # Прочитать данные из существующего файла
                with open(existing_file_path, 'r') as json_file:
                    existing_data = json.load(json_file)
            except json.decoder.JSONDecodeError:
                print(f"Error decoding JSON in {existing_file_path}. Creating a new empty dictionary.")
                existing_data = {}
            except FileNotFoundError:
                print(f"File {existing_file_path} not found. Creating a new empty dictionary.")
                existing_data = {}

            existing_data.update(date_to_save)

            with open(existing_file_path, 'w') as file:
                json.dump(existing_data, file, indent=4)
        except Exception as e:
            self.logger.error(f'An error occurred in MyExtension: {str(e)}')
