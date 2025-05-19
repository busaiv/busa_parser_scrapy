import random
import json

class ProxyMiddleware:
    def __init__(self, proxies):
        self.proxies = proxies

    @classmethod
    def from_crawler(cls, crawler):
        with open('proxies.json', encoding='utf-8') as f:
            proxies = [proxy for proxy in json.load(f) if proxy and proxy.startswith('https://')]

        return cls(proxies)

    def process_request(self, request, spider):
        proxy = random.choice(self.proxies)
        spider.logger.info(f'using proxy: {proxy}')
        request.meta['proxy'] = proxy
