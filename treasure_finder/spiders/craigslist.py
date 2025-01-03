import scrapy
import json
import re
import time
import random


class CraigslistSpider(scrapy.Spider):
    name = "craigslist"
    allowed_domains = ["vancouver.craigslist.org"]
    start_urls = ["https://vancouver.craigslist.org/search/apa?format=html"]

    def parse(self, response):
        listings = response.xpath('//ol[@class="cl-static-search-results"]/li[position()>1]')
        
        for listing in listings:
            url = listing.xpath('.//a/@href').get(default='')
            item = {
                'source': 'craigslist',
                'title': listing.xpath('@title').get(default='No title'),
                'url': url,
                'price': listing.xpath('.//div[@class="price"]/text()').get(default=''),
                'location': listing.xpath('.//div[@class="location"]/text()').get(default='').strip(),
                'imageUrl': None,
                'bedrooms': None,
                'bathrooms': None,
                'type': None,
                'size': None,
                'aircon': None,
                'furnished': None,
                'parking': None,
            }
            
            # random delay to avoid being blocked
            time.sleep(1)
            
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta={'item': item}
            )

    def parse_detail(self, response):
        item = response.meta['item']
        # parse image url
        item['imageUrl'] = response.xpath('//meta[@property="og:image"]/@content').get()
        if not item['imageUrl']:
            img_list_pattern = r'var\s+imgList\s*=\s*(\[.*?\]);'
            img_list_match = re.search(img_list_pattern, response.text, re.DOTALL)
            if img_list_match:
                try:
                    img_list = json.loads(img_list_match.group(1))
                    if img_list:
                        item['imageUrl'] = img_list[0]['url']
                except json.JSONDecodeError:
                    pass

        # parse type, bedrooms, bathrooms from JSON
        posting_data = response.xpath('//script[@id="ld_posting_data"]/text()').get()
        if posting_data:
            try:
                data = json.loads(posting_data)
                
                # parse bedrooms
                bedrooms = data.get('numberOfBedrooms')
                if bedrooms:
                    item['bedrooms'] = float(bedrooms)
                
                # parse bathrooms
                bathrooms = data.get('numberOfBathroomsTotal')
                if bathrooms:
                    item['bathrooms'] = float(bathrooms)
                
                # parse type
                item['type'] = data.get('@type')
                
            except (json.JSONDecodeError, ValueError):
                pass

        # parse size from attrgroup
        attrs = response.css('.attrgroup .attr.important::text').getall()
        for attr in attrs:
            attr = attr.strip()
            if 'ft' in attr:
                match = re.search(r'(\d+)ft', attr)
                if match:
                    item['size'] = float(match.group(1))
        
        # parse facilities from the third attrgroup div
        attrgroup = response.xpath('(//div[@class="attrgroup"])[3]')
        if attrgroup:
            # Check for air conditioning
            item['aircon'] = bool(attrgroup.xpath('.//div[contains(@class, "attr airconditioning")]'))
            
            # Check for furnished
            item['furnished'] = bool(attrgroup.xpath('.//div[contains(@class, "attr is_furnished")]'))
            
            # Check for parking
            parking_link = attrgroup.xpath('.//a[contains(@href, "/search/apa?parking=")]').get()
            item['parking'] = bool(parking_link and re.search(r'/search/apa\?parking=[123]', parking_link))

        yield item

