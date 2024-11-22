import scrapy
import json
from parsel import Selector

class VanpeopleSpider(scrapy.Spider):
    name = "vanpeople"
    allowed_domains = ["c.vanpeople.com"]
    start_urls = [f"https://c.vanpeople.com/zufang/?page={i}" for i in range(1, 6)]

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

    def parse(self, response):
        listings = response.xpath('//li[@class="list" or @class="list "][not(.//div[@class="c-list-pic fl"]//span[text()="推广"])]')
        
        for listing in listings:
            item = {
                'title': listing.xpath('.//a[@class="c-list-title"]/text()').get(default='No title').strip(),
                'url': listing.xpath('.//a[@class="c-list-title"]/@href').get(default=''),
                'price': listing.xpath('.//div[@class="c-list-money"]//span[@class="money"]/text()').get(default='No money').strip(),
                'tips': ' '.join(listing.xpath('.//div[@class="c-list-tips"]//span/text()').getall()).strip(),
                'date': listing.xpath('.//div[@class="c-list-contxt-r"]//span[@class="c-list-date"]/text()').get(default='No time').strip()
            }
            yield item
