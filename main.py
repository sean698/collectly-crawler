import base64
import functions_framework
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from treasure_finder.spiders.vanpeople import VanpeopleSpider
from treasure_finder.spiders.craigslist import CraigslistSpider

@functions_framework.cloud_event
def run_spiders(cloud_event):
    message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode('utf-8')
    try:
       print('Spider process starting...')
       process = CrawlerProcess(get_project_settings())

       process.crawl(VanpeopleSpider)
       process.crawl(CraigslistSpider)
       
       process.start()
       print('Spider process completed')
    except Exception as e:
       print(f"Error in run_spiders: {e}")

