import scrapy
import json


class CraigslistSpider(scrapy.Spider):
    name = "craigslist"
    allowed_domains = ["vancouver.craigslist.org"]
    # change the url
    start_urls = ["https://vancouver.craigslist.org/search/bnc/apa?format=html"]

    def parse(self, response):
        listings = response.xpath('//ol[@class="cl-static-search-results"]/li[position()>1]')
        
        for listing in listings:
            item = {
                'title': listing.xpath('@title').get(default='No title'),
                'url': listing.xpath('.//a/@href').get(default=''),
                'price': listing.xpath('.//div[@class="price"]/text()').get(default=''),
                'location': listing.xpath('.//div[@class="location"]/text()').get(default='').strip()
            }
            yield item