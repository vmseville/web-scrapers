from shutil import which
from functools import wraps
import urllib.parse
import logging

from bs4 import BeautifulSoup

from scrapy.spiders import CrawlSpider
from scrapy.item import Item, Field
from scrapy_selenium import SeleniumRequest

logger = logging.getLogger('spider_logger')

class SearchItem(Item):
    """Structure of item data to be extracted."""
    name = Field()
    price = Field()
    pcs_sold = Field()
    url = Field()


class ItemSpider(CrawlSpider):
    base_url = "https://shopee.ph"

    name = 'shopee_spider'
    allowed_domain = ['shopee.ph']
    custom_settings = {
        'BOT_NAME': 'shopee scraper bot',
        #added necessary settings for scrapy-selenium
        #this sets chrome as the webdriver for the selenium browser automation
        'SELENIUM_DRIVER_NAME': 'chrome',
        'SELENIUM_DRIVER_EXECUTABLE_PATH': which('chromedriver'),
        'SELENIUM_DRIVER_ARGUMENTS': ['--headless'],
        'DOWNLOADER_MIDDLEWARES': { 'scrapy_selenium.SeleniumMiddleware': 800 }
    }

    def handle_thousand(function):
        """Decorator function to handle values in thousands.
        
        When pieces sold for an item reach thousand/s, text amount would
        contain 'K' suffix to denote thousand instead of full amount
        e.g. 1500 = "1.5K", 7300 = "7.3K" 
        
        This is also to utilize decorator as an advanced Python feature.
        """
        @wraps(function)
        def wrapper(*args, **kwargs):
            amount_string = function(*args, **kwargs)

            if 'K' in amount_string:
                return float(amount_string.replace('K', '')) * 1000

            return amount_string

        return wrapper

    @handle_thousand
    def convert_sold_info(self, sold_info):
        """Remove the ' sold' from the text value for pieces sold info"""
        if sold_info.string:
            return sold_info.string.replace(' sold', '')
        else:
            return str(0)

    def start_requests(self):
        """Generates the Request object for this spider to crawl.
        Note that this is a SeleniumRequest (the Request subclass when utilizing scrapy-selenium).
        """
        yield SeleniumRequest(url=f'https://shopee.ph/search?keyword={self.item}', callback=self.parse)

    def parse(self, response):
        """Parses the response using BeautifulSoup.
        Necessary data is then extracted for each item according to SearchItem data structure.
        """
        html_content = BeautifulSoup(response.body, "html.parser")
        items = html_content.find_all(class_="shopee-search-item-result__item")

        for item in items:
            search_item = SearchItem()
            sold_info = item.find(class_="go5yPW")
            pcs_sold = 0

            if sold_info:
                pcs_sold = int(self.convert_sold_info(sold_info))

            #only extract items with pieces sold amount higher than inputted min_sold argument 
            if pcs_sold >= int(self.min_sold):
                price = float(item.find(class_="_29R_un").string.replace(',', ''))
                formatted_price = "P{:,.2f}".format(price)

                search_item['name'] = item.find(class_="yQmmFK _1POlWt _36CEnF").string
                search_item['price'] = formatted_price
                search_item['pcs_sold'] = pcs_sold
                search_item['url'] = f"{self.base_url}{urllib.parse.quote(item.a['href'])}"
                
                yield search_item


