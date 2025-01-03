import scrapy
import json
from parsel import Selector
import re

class VanpeopleSpider(scrapy.Spider):
    name = "vanpeople"
    allowed_domains = ["c.vanpeople.com"]

    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://vanpeople.com/'
        }
    }

    # change end page
    def __init__(self, category='zufang', startPage=1, endPage=4, location='', *args, **kwargs):
        super(VanpeopleSpider, self).__init__(*args, **kwargs)
        self.category = category
        self.startPage = int(startPage)
        self.endPage = int(endPage)
        self.location = location
        self.start_urls = [
            f"https://c.vanpeople.com/{self.category}/?page={i}" 
            for i in range(self.startPage, self.endPage + 1)
        ]

    def get_image_url(self, listing):
        img_url = listing.xpath('.//div[@class="c-list-pic fl"]//img/@data-original').get()
        if not img_url:
            img_url = listing.xpath('.//div[@class="c-list-pic fl"]//img/@src').get()
        return img_url or 'No image'

    def parse_house_info(self, listing):
        """Parse house type, bedrooms and bathrooms from listing tips"""
        tips = listing.xpath('.//div[@class="c-list-tips"]//span/text()').getall()
        
        house_info = {
            'type': None,
            'bedrooms': None,
            'bathrooms': None
        }
        
        # Dictionary to map Chinese house types to English
        type_mapping = {
            '独立屋': 'House',
            '连排屋': 'Townhouse',
            '公寓': 'Apartment',
            '地下室': 'Basement',
        }
        
        for tip in tips:
            tip = tip.strip()
            # Parse house type
            if tip in type_mapping:
                house_info['type'] = type_mapping[tip]
            
            # Parse bedrooms
            if '卧' in tip:
                try:
                    house_info['bedrooms'] = float(re.search(r'(\d+)卧', tip).group(1))
                except (AttributeError, ValueError):
                    pass
            
            # Parse bathrooms
            if '卫' in tip:
                try:
                    house_info['bathrooms'] = float(re.search(r'(\d+)卫', tip).group(1))
                except (AttributeError, ValueError):
                    pass
        
        return house_info

    def parse(self, response):
        listings = response.xpath('//li[@class="list" or @class="list "][not(.//div[@class="c-list-pic fl"]//span[text()="推广"])][not(.//div[@class="c-list-pic fl"]//span[text()="推荐"])]')
        
        for listing in listings:
            relative_url = listing.xpath('.//a[@class="c-list-title"]/@href').get(default='')
            full_url = f"https://c.vanpeople.com{relative_url}" if relative_url else ''

            tips = listing.xpath('.//div[@class="c-list-tips"]//span/text()').getall()
            location = tips[0].strip() if tips else 'No location'
            
            # Get house info including type, bedrooms and bathrooms
            house_info = self.parse_house_info(listing)
            
            item = {
                'source': 'vanpeople',
                'title': listing.xpath('.//a[@class="c-list-title"]/text()').get(default='No title').strip(),
                'url': full_url,
                'price': listing.xpath('.//div[@class="c-list-money"]//span[@class="money"]/text()').get(default='No money').strip(),
                'location': location,
                'imageUrl': self.get_image_url(listing),
                'type': house_info['type'],
                'bedrooms': house_info['bedrooms'],
                'bathrooms': house_info['bathrooms'],
                'size': None,
                'furnished': None,
                'parking': None,
                'aircon': None,
            }

            yield scrapy.Request(
                url=full_url,
                callback=self.parse_detail,
                meta={'item': item}
            )

    def parse_detail(self, response):
        item = response.meta['item']
        
        # Get all facility items in the device section
        facilities = response.xpath('//div[contains(@class, "info-detail-device")]//li/p/text()').getall()
        facilities = [f.strip() for f in facilities if f.strip()]
        
        # Check for specific facilities
        item['furnished'] = '基本家具' in facilities
        item['parking'] = '独立车位' in facilities
        item['aircon'] = '中央空调' in facilities
            
        yield item


