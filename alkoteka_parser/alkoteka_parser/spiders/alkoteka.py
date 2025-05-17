import scrapy
import json
import time


class AlkotekaSpider(scrapy.Spider):
    name = 'alkoteka'
    allowed_domains = ['alkoteka.com']
    city = '4a70f9e0-46ae-11e7-83ff-00155d026416'
    categories_file = 'categories.json'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = 0

    async def start(self):

        with open(self.categories_file, encoding='utf-8') as f:
            categories = json.load(f)

        for category in categories:
            slug = category['url'].rstrip('/').split('/')[-1]
            api_url = (f'https://alkoteka.com/web-api/v1/product?city_uuid={self.city}'
                       f'&page=1&per_page=20&root_category_slug={slug}')
            yield scrapy.Request(api_url, callback=self.parse_category, meta={'slug': slug, 'page': 1})

    def parse_category(self, response):
        data = json.loads(response.text)
        results = data.get('results', [])
        slug = response.meta['slug']
        page = response.meta['page']

        for product in results:
            #self.count += 1
            #if self.count % 50 == 0:
                #self.logger.info(f'count: {self.count}')

            yield {
                "timestamp": int(time.time()),
                "RPC": str(product.get("vendor_code", "")),
                "url": product.get("product_url"),
                "title": product.get("name"),
                "marketing_tags": [tag.get("title") for tag in product.get("action_labels", [])],
                "brand": "",
                "section": [slug],
                "price_data": {
                    "current": product.get("price", 0),
                    "original": product.get("prev_price") or product.get("price", 0),
                    "sale_tag": "",
                },
                "stock": {
                    "in_stock": product.get("available", False),
                    "count": product.get("quantity_total", 0),
                },
                "assets": {
                    "main_image": product.get("image_url"),
                    "set_images": [],
                    "view360": [],
                    "video": [],
                },
                "metadata": {

                },
                "variants": 0,
            }

        if results:
            next_page = page + 1
            next_url = (f'https://alkoteka.com/web-api/v1/product?city_uuid={self.city}&page={next_page}'
                        f'&per_page=20&root_category_slug={slug}')
            yield scrapy.Request(next_url, callback=self.parse_category, meta={'slug': slug, 'page': next_page})

        #def close(spider):
            #spider.logger.info(f'total: {self.count}')
            #spider.logger.info(f'close: {spider.name}')

    def parse_product(self, response):
        pass

