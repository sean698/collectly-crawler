import scrapy
import json
from parsel import Selector

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

    def __init__(self, category='zufang', startPage=1, endPage=3, location='', *args, **kwargs):
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

    def parse(self, response):
        listings = response.xpath('//li[@class="list" or @class="list "][not(.//div[@class="c-list-pic fl"]//span[text()="推广"])]')
        
        for listing in listings:
            relative_url = listing.xpath('.//a[@class="c-list-title"]/@href').get(default='')
            full_url = f"https://c.vanpeople.com{relative_url}" if relative_url else ''

            tips = listing.xpath('.//div[@class="c-list-tips"]//span/text()').getall()
            location = tips[0].strip() if tips else 'No location'
            remaining_tips = ' '.join(tips[1:]).strip() if len(tips) > 1 else ''
            
            item = {
                'source': 'vanpeople',
                'title': listing.xpath('.//a[@class="c-list-title"]/text()').get(default='No title').strip(),
                'url': full_url,
                'price': listing.xpath('.//div[@class="c-list-money"]//span[@class="money"]/text()').get(default='No money').strip(),
                'location': location,
                'tips': remaining_tips,
                'date': listing.xpath('.//div[@class="c-list-contxt-r"]//span[@class="c-list-date"]/text()').get(default='No time').strip(),
                'imageUrl': self.get_image_url(listing)
            }
            yield item
