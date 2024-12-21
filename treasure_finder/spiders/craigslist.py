import scrapy
import json
import re
import base64
from firebase_admin import firestore


class CraigslistSpider(scrapy.Spider):
    name = "craigslist"
    allowed_domains = ["vancouver.craigslist.org"]
    start_urls = ["https://vancouver.craigslist.org/search/apa?format=html"]

    def parse(self, response):
        listings = response.xpath('//ol[@class="cl-static-search-results"]/li[position()>1]')
        
        # Get Firestore client
        db = firestore.client()
        collection_ref = db.collection('rental_listings')
        
        for listing in listings:
            url = listing.xpath('.//a/@href').get(default='')
            if not url:
                continue
                
            # Generate document ID same way as pipeline
            doc_id = base64.urlsafe_b64encode(url.encode()).decode()
            
            # Check if listing exists in database
            doc = collection_ref.document('craigslist').collection('listings').document(doc_id).get()
            
            if not doc.exists:
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
                    'size': None
                }
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                    meta={'item': item}
                )
            else:
                print(f"Listing already exists in database (craigslist)")

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
        
        yield item

