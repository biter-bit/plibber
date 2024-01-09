from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from parse_social_media.spiders.vk_parse import VkParseSpider
from parse_social_media import settings

if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(VkParseSpider)

    process.start()
