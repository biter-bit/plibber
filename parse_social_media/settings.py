import os

PATH_BASE = os.getcwd()

BOT_NAME = "parse_social_media"

SPIDER_MODULES = ["parse_social_media.spiders"]
NEWSPIDER_MODULE = "parse_social_media.spiders"

LOG_ENABLED = True
LOG_LEVEL = "DEBUG"
# LOG_FILE = f'{PATH_BASE}/logs/spider.log'

FILES_STORE = 's3://24825ad4-e2369fbe-f825-4ba9-9c6e-f9de1573149f/files'
IMAGES_STORE = 's3://24825ad4-e2369fbe-f825-4ba9-9c6e-f9de1573149f/photos'
AWS_ENDPOINT_URL = 'https://s3.timeweb.cloud'
AWS_ACCESS_KEY_ID = 'SI3PXEYPDWJK5AXJ1JQK'
AWS_SECRET_ACCESS_KEY = '1HUe80GXLnQ2uxXEg6ijz5D6JAAJ8RCwThr3gKsr'
AWS_REGION_NAME = 'ru-1'

#  размер сжатия картинок (от 1 до 100)
IMAGES_JPEG_QUALITY = 30

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "parse_social_media (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 10

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 1
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "parse_social_media.middlewares.ParseSocialMediaSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
    'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
}

# Proxy
# ROTATING_PROXY_PAGE_RETRY_TIMES = 5
# ROTATING_PROXY_PAGE_RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]
# ROTATING_PROXY_LIST_PATH = f'{PATH_BASE}/proxys.txt'
ROTATING_PROXY_LIST = []
RETRY_TIMES = 100

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    # 'parse_social_media.extensions.MyExtension': 500,
    'scrapy.extensions.closespider.CloseSpider': 500,
    "scrapy.extensions.telnet.TelnetConsole": None,
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "parse_social_media.pipelines.ParseSocialMediaPipeline": 600,
    # "parse_social_media.pipelines.ParseSocialMediaGroupsPipelines": 500,
    # "parse_social_media.pipelines.ParseSocialMediaPostsPipelines": 400,
    "parse_social_media.pipelines.ParseSocialMediaPhotosPipeline": 300,
    # "parse_social_media.pipelines.ParseSocialMediaVideosPipelines": 200,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

CLOSESPIDER_PAGECOUNT = 0
