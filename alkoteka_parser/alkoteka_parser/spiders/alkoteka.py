import json
import time

import scrapy


class AlkotekaSpider(scrapy.Spider):
    name = 'alkoteka'
    allowed_domains = ['alkoteka.com']
    city = '4a70f9e0-46ae-11e7-83ff-00155d026416'
    categories_file = 'categories.json'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = 0

    def start_requests(self):

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
        total_items = data.get('meta')['total']
        per_page = data.get('meta')['per_page']

        max_pages = (total_items + per_page - 1) // per_page

        #self.logger.info(f"Category {slug}: page {page} of {max_pages} (total items: {total_items})")


        for product in results:
            item = {
                'timestamp': int(time.time()),
                'RPC': str(product.get('vendor_code', "")),
                'url': product.get('product_url'),
                'title': f"{product.get('name')}, {product.get('filter_labels')[0].get('title')}",
                'marketing_tags': [tag.get('title') for tag in product.get('action_labels', [])],
                'brand': "",
                'section': [slug],
                'price_data': {
                    'current': product.get('price', 0),
                    'original': product.get('prev_price') or product.get('price', 0),
                    'sale_tag': (
                        f"discount {round((product.get('prev_price', 0) - product.get('price', 0)) /
                                          product.get('prev_price', 1) * 100)}%"
                        if product.get('prev_price') and product.get('prev_price') > product.get('price', 0) else ''
                    ),
                },
                'stock': {
                    'in_stock': product.get('available', False),
                    'count': product.get('quantity_total', 0),
                },
                'assets': {
                    'main_image': product.get('image_url'),
                    'set_images': [],
                    'view360': [],
                    'video': [],
                },
                'metadata': {

                },
                'variants': 0,
            }

            yield scrapy.Request(
                url=f"https://alkoteka.com/web-api/v1/product/"
                    f"{product.get('slug')}?city_uuid={self.city}",
                callback=self.parse_product,
                meta={'item': item}
            )

        if page < max_pages:
            next_page = page + 1
            next_url = (f'https://alkoteka.com/web-api/v1/product?city_uuid={self.city}&page={next_page}'
                        f'&per_page=20&root_category_slug={slug}')
            yield scrapy.Request(
                next_url,
                callback=self.parse_category,
                meta={'slug': slug, 'page': next_page},
                dont_filter=False
            )

    def parse_product(self, response):
        item = response.meta['item']
        data = json.loads(response.text)

        product = data.get('results', {})

        item['metadata'] = {'description': product.get('text_blocks')[0].get('content', '')
        if len(product.get('text_blocks')) > 0 else ''}
        item['metadata'].update({f.get('filter'): f.get('title') for f in product.get('filter_labels', []) if
                                 f.get('filter') and f.get('title')})
        #self.count += 1
        #self.logger.info(f"Products processed: {self.count}")

        yield item
