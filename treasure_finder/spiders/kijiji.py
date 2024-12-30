import scrapy
import json
from datetime import datetime
from ..constants import LOCATION_MAP
from firebase_admin import firestore


class KijijiSpider(scrapy.Spider):
    name = "kijiji"
    allowed_domains = ["kijiji.ca"]

    def __init__(self, startPage=1, endPage=2, radius=40, *args, **kwargs):
        super(KijijiSpider, self).__init__(*args, **kwargs)
        self.startPage = int(startPage)
        self.endPage = int(endPage)
        self.radius = radius
        self.start_urls = [
            f"https://www.kijiji.ca/b-apartments-condos/vancouver/page-{i}/c37l1700287?address=Vancouver%2C%20BC&ll=49.2827291%2C-123.1207375&radius={self.radius}"
            for i in range(self.startPage, self.endPage + 1)
        ]

    def parse(self, response):
        script_data = response.xpath('//script[@type="application/ld+json"]/text()').get()
        if script_data:
            data = json.loads(script_data)
            if 'itemListElement' in data:
                listings = data['itemListElement']
                
                for listing in listings:
                    item_data = listing.get('item', {})
                    url = item_data.get('url')
                    
                    if not url:
                        continue
                        
                    item = {
                        'source': 'kijiji',
                        'title': item_data.get('name'),
                        'description': item_data.get('description'),
                        'url': url,
                        'location': item_data.get('address'),
                        'price': None,
                        'bedrooms': float(item_data.get('numberOfBedrooms')) if item_data.get('numberOfBedrooms') else None,
                        'bathrooms': float(item_data.get('numberOfBathroomsTotal')) if item_data.get('numberOfBathroomsTotal') else None,
                        'size': float(item_data.get('floorSize', {}).get('value')) if item_data.get('floorSize', {}).get('value') else None,
                        'imageUrl': item_data.get('image'),
                        'type': None
                    }
                    
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_detail,
                        meta={'item': item}
                    )

    def parse_detail(self, response):
        item = response.meta['item']
        
        # parse price
        item['price'] = response.css('span[itemprop="price"]::text').get()
        
        # parse type
        type_element = response.css('div[class*="titleAttributes-"] li:first-child span::text').get()
        if type_element:
            item_type = type_element.strip()
            item['type'] = 'Apartment' if item_type == 'Condo' else item_type

        yield item
