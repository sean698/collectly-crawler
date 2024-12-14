import scrapy
import json
from datetime import datetime


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

    def parse(self, response):
        listings = response.css('li[data-testid*="listing-card-list-item-"]')
        
        for listing in listings:
            item = {
                'source': 'kijiji',
                'imageUrl': listing.css('[data-testid="listing-card-image"]::attr(src)').get(),
                'price': listing.css('[data-testid="listing-price"]::text').get(),
                'title': listing.css('[data-testid="listing-link"]::text').get(),
                'url': listing.css('[data-testid="listing-link"]::attr(href)').get(),
                'location': listing.css('[data-testid="listing-location"]::text').get(),
                'description': listing.css('[data-testid="listing-description"]::text').get()
            }
            yield item
