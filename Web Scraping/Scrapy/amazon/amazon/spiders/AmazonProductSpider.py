import scrapy
from amazon.items import AmazonItem
from scrapy_selenium import SeleniumRequest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# RUN VIA FOLLOWING COMMAND:
#  scrapy crawl AmazonDeals -o items.csv

class AmazonProductSpider(scrapy.Spider):
    name = "AmazonDeals"
    allowed_domains = ["amazon.co.uk"]
    start_urls = ["https://www.amazon.co.uk/Lessons-Chemistry-Sunday-bestseller-Between/dp/1804990922/ref=zg_bs_books_sccl_1/257-9642007-7649509?psc=1",
                  "https://www.amazon.co.uk/Bullet-That-Missed-Thursday-Murder/dp/0241992389/ref=zg_bs_books_sccl_2/257-9642007-7649509?psc=1",
                  "https://www.amazon.co.uk/Ultra-Processed-People-Stuff-That-Isnt/dp/1529900050/ref=zg_bs_books_sccl_3/257-9642007-7649509?psc=1",
                  "https://www.amazon.co.uk/Extra-Mile-My-Autobiography/dp/152990305X/ref=zg_bs_books_sccl_4/257-9642007-7649509?psc=1"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        service = Service("../chromedriver_win32")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1200")
        self.driver = webdriver.Chrome(service=service, options=options)

    # def start_requests(self):
    #     for url in self.start_urls:
    #         yield SeleniumRequest(url=url, callback=self.parse)

    def parse(self, response):
        items = AmazonItem()
        self.driver.get(response.url)
        # title = response.xpath('//h1[@id="title"]/span/text()').extract()
        # sale_price = response.xpath('//span[contains(@id,"ourprice") or contains(@id,"saleprice")]/text()').extract()
        # category = response.xpath('//a[@class="a-link-normal a-color-tertiary"]/text()').extract()
        # availability = response.xpath('//div[@id="availability"]//text()').extract()
        title = self.driver.find_element(By.XPATH, '//h1[@id="title"]/span')
        sale_price = self.driver.find_element(By.XPATH, '//span[contains(@id,"ourprice") or contains(@id,"saleprice")]')
        category = self.driver.find_element(By.XPATH, '//a[@class="a-link-normal a-color-tertiary"]')
        availability = self.driver.find_element(By.XPATH, '//div[@id="availability"]/')
        items['product_name'] = ''.join(title).strip()
        items['product_sale_price'] = ''.join(sale_price).strip()
        items['product_category'] = ','.join(map(lambda x: x.strip(), category)).strip()
        items['product_availability'] = ''.join(availability).strip()
        yield items