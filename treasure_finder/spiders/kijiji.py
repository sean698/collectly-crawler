import scrapy
import json
from datetime import datetime
import re


class KijijiSpider(scrapy.Spider):
    name = "kijiji"
    allowed_domains = ["kijiji.ca"]

    def __init__(self, startPage=1, endPage=3, radius=30, *args, **kwargs):
        super(KijijiSpider, self).__init__(*args, **kwargs)
        self.startPage = int(startPage)
        self.endPage = int(endPage)
        self.radius = radius
        self.start_urls = [
            f"https://www.kijiji.ca/b-apartments-condos/vancouver/page-{i}/c37l1700287?address=Vancouver%2C%20BC&ll=49.2827291%2C-123.1207375&radius={self.radius}"
            for i in range(self.startPage, self.endPage + 1)
        ]
        self.items = []
        self.filename = f"kijiji_{datetime.utcnow().isoformat().replace(':', '-')}.json"

    def parse(self, response):
        print(f"Parsing URL: {response.url}")
        
        with open('kijiji.html', 'w', encoding='utf-8') as file:
            file.write(response.text)
            
        script_data = response.xpath('//script[@type="application/ld+json"]/text()').get()
        if script_data:
            try:
                data = json.loads(script_data)
                if 'itemListElement' in data:
                    listings = data['itemListElement']
                    
                    for listing in listings:
                        item_data = listing.get('item', {})
                        item = {
                            'source': 'kijiji',
                            'title': item_data.get('name'),
                            'description': item_data.get('description'),
                            'url': item_data.get('url'),
                            'location': item_data.get('address'),
                            'price': None,
                            'bedrooms': item_data.get('numberOfBedrooms'),
                            'bathrooms': item_data.get('numberOfBathroomsTotal'),
                            'size': item_data.get('floorSize', {}).get('value'),
                            'image': item_data.get('image')
                        }
                        
                        if item['url']:
                            yield scrapy.Request(
                                url=item['url'],
                                callback=self.parse_detail,
                                meta={'item': item}
                            )
                        
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")

    # parse detail page to get price
    def parse_detail(self, response):
        item = response.meta['item']
        item['price'] = response.css('span[itemprop="price"]::text').get()
        
        self.items.append(item)
        yield item

