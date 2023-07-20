import csv
from datetime import datetime
import time

import numpy as np
import pandas as pd
# https://www.youtube.com/watch?v=HiOtQMcI5wg
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import requests

def scroll_to_bottom(driver):
# https://stackoverflow.com/questions/32391303/how-to-scroll-to-the-end-of-the-page-using-selenium-in-python
    old_position = 0
    new_position = None

    while new_position != old_position:
        # Get old scroll position
        old_position = driver.execute_script(
                ("return (window.pageYOffset !== undefined) ?"
                 " window.pageYOffset : (document.documentElement ||"
                 " document.body.parentNode || document.body);"))
        # Sleep and Scroll
        time.sleep(2)
        driver.execute_script((
                "var scrollingElement = (document.scrollingElement ||"
                " document.body);scrollingElement.scrollTop ="
                " scrollingElement.scrollHeight;"))
        # Get new position
        new_position = driver.execute_script(
                ("return (window.pageYOffset !== undefined) ?"
                 " window.pageYOffset : (document.documentElement ||"
                 " document.body.parentNode || document.body);"))

links = ["https://www.amazon.co.uk/Best-Sellers-Books-Role-Playing-War-Games/zgbs/books/270509/ref=zg_bs_nav_books_3_270453",
         "https://www.amazon.co.uk/best-sellers-books-Amazon/zgbs/books/270509/ref=zg_bs_pg_2_books?_encoding=UTF8&pg=2",
         "https://www.amazon.co.uk/gp/bestsellers/books/503400/ref=pd_zg_hrsr_books",
         "https://www.amazon.co.uk/best-sellers-books-Amazon/zgbs/books/503400/ref=zg_bs_pg_2_books?_encoding=UTF8&pg=2",
         "https://www.amazon.co.uk/gp/bestsellers/books/14909604031/ref=pd_zg_hrsr_books",
         "https://www.amazon.co.uk/best-sellers-books-Amazon/zgbs/books/14909604031/ref=zg_bs_pg_2_books?_encoding=UTF8&pg=2"]

def create_blank_csv(file_name, createHeader=False):
    if createHeader==True:
        header = ["Title", "Link", "Edition Format"]
        with open(file_name, "w", newline="", encoding="UTF8") as f:
           writer = csv.writer(f)
           writer.writerow(header)
    else:
        with open(file_name, "w", newline="", encoding="UTF8") as f:
           writer = csv.writer(f)


def setup_list_one_page_from_amazon(file_name, URL=None):
    service = Service("..\chromedriver_win32")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1200")
    driver = webdriver.Chrome(service=service, options=options)
    if URL == None:
        URL = "https://www.amazon.co.uk/gp/bestsellers/books"
    driver.get(URL)

    # Accept Cookies
    wait = WebDriverWait(driver, 10)
    try:
        # https://stackoverflow.com/questions/67274590/click-accept-cookies-popup-with-selenium-in-python
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sp-cc-accept"]')))
        driver.find_element("xpath", '//*[@id="sp-cc-accept"]').click()
    except:
        print("Cookies timeout!")

    scroll_to_bottom(driver)

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, features="lxml")
    results = soup.find("div", class_="p13n-desktop-grid")

    books_html = results.findAll("div", id="gridItemRoot")
    counter = 0

    for book_element in books_html:
        counter += 1
        print(counter)

        # title
        span_element = book_element.findAll("div", class_="_cDEzb_p13n-sc-css-line-clamp-1_1Fn1y")
        # author = span_element[1].get_text()
        if not span_element:
            print("IF STATEMENT")
            span_element = book_element.findAll("div", class_="_cDEzb_p13n-sc-css-line-clamp-2_EWgCb")
            if not span_element:
                print("IF2 STATEMENT")
                span_element = book_element.findAll("div", class_="_cDEzb_p13n-sc-css-line-clamp-3_g3dy1")
                if not span_element:
                    print("IF3 STATEMENT")
                    span_element = book_element.findAll("div", class_="_cDEzb_p13n-sc-css-line-clamp-4_2q2cc")
        if len(span_element) != 0 :
            title = span_element[0].get_text()
            print(title)
        else:
            print("ERROR! Counter: ", counter)
            title = ""


        # link
        link_element = book_element.find("a", class_="a-link-normal")
        href = link_element["href"]
        link = "amazon.co.uk" + href
        print(link)

        # Edition Format
        edition_element = book_element.find("span", class_="a-size-small a-color-secondary a-text-normal")
        edition_format_text = edition_element.get_text()
        print(edition_format_text)

        if edition_format_text=="Paperback" or edition_format_text=="Hardcover":
            data = [title, link, edition_format_text]

            with open(file_name, "a+", newline="", encoding="UTF8") as f:
                    writer = csv.writer(f)
                    writer.writerow(data)
        else:
            print("Book not saved to list of books.")


# Get ISBN from the second column of a CSV.
def get_ISBN_from_list(file_name):
    pd.set_option('display.max_rows', 1000)
    pd.options.display.width = 0

    df = pd.read_csv(file_name)

    links_column = df.iloc[:,[1]]
    number_of_rows = df.shape[0]
    isbn_list = []

    for row_number in range(number_of_rows):
        row = df.iloc[row_number,[1]]
        string_row = row[0]
        index_of_dp = string_row.find("dp/")
        rest_of_string = string_row[(index_of_dp+3):]
        isbn_number = rest_of_string[:10]
        isbn_list.append(isbn_number)

    df["ISBN"] = isbn_list
    df.to_csv(file_name, index=False)


def check_amazon_prices_today(file_name, URL=None):
    now = datetime.now()
    current_date = now.strftime("%d/%m/%Y")

    new_product_prices_list = []
    new_delivery_prices_list = []
    used_product_prices_list = []
    used_delivery_prices_list = []

    df = pd.read_csv(file_name)
    number_of_rows = df.shape[0]

    service = Service("..\chromedriver_win32")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument('--blink-settings=imagesEnabled=false')
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    for row_number in range(number_of_rows):
        isbn = df.shape[row_number][1]
        time1 = datetime.now()
        print("Item: " + str(row_number))
        URL_raw = df.iloc[row_number, [1]]
        URL = "https://www." + URL_raw[0]

        print(URL)

        driver = webdriver.Chrome(service=service, options=options)
        driver.get(URL)
        html = driver.page_source
        driver.quit()
        soup = BeautifulSoup(html, features="lxml")

        # New Product Price
        results = soup.find("span", id="price")
        if results is not None:
            price = results.get_text()
            price_without_sign = price[1:]
            new_product_prices_list.append(price_without_sign)
            print("New Product Price: ", price_without_sign)
        else:
            new_product_prices_list.append(999999)
            print("New Product Price: FAIL")


        # New Delivery Price
        try:
            pass
        except:
            new_product_prices_list.append(999999)
            print("New Delivery Price: FAIL")


        # Used Product Price
        try:
            URL = "https://www.amazon.co.uk/dp/" + isbn + "/ref=olp-opf-redir?aod=1&ie=UTF8&condition=used"
            driver.get(URL)
            html = driver.page_source
            driver.quit()
            soup = BeautifulSoup(html, features="lxml")
            results = soup.find("span", id="price")

        except:
            new_product_prices_list.append(999999)
            print("Used Product Price: FAIL")


        # Used Delivery Price
        try:
            pass
        except:
            new_product_prices_list.append(999999)
            print("Used Delivery Price: FAIL")

        time2 = datetime.now()
        time_diff = time2 - time1
        print("Time: ", time_diff.seconds)
        print()

    df["New Product Price"] = new_product_prices_list
    df["New Delivery Price"] = new_delivery_prices_list
    df["New Total Price"] = new_product_prices_list + new_delivery_prices_list
    df["Used Product Price"] = used_product_prices_list
    df["Used Delivery Price"] = used_delivery_prices_list
    df["Used Total Price"] = used_product_prices_list + used_delivery_prices_list
    df.to_csv(file_name, index=False)


def check_ebay_prices_today(file_name):
    # MAKE SURE ISBN-10s WITHIN SOURCE CSV ARE FORMATTED WITH LEADING ZEROES INCLUDED
    now = datetime.now()
    current_date = now.strftime("%d/%m/%Y")

    df = pd.read_csv(file_name)
    number_of_rows = df.shape[0]
    isbn_col = df.iloc[:, [2]]
    ebay_price_list = []

    for row_number in range(number_of_rows):
        isbn_for_row = (df.iloc[row_number, [2]])[0]
        full_isbn = isbn_for_row.zfill(10)

        URL = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
            full_isbn) + "&_sacat=0&_sop=15&LH_ItemCondition=3&LH_PrefLoc=2&rt=nc&LH_BIN=1"
        print(URL)
        page = requests.get(URL)
        html = page.text
        soup = BeautifulSoup(html, features="lxml")
        try:
            results = soup.find("ul", class_="srp-results")
            books_html = results.findAll("span", class_="s-item__price")
            lowest_price_with_sign = books_html[0].get_text()
            lowest_price = lowest_price_with_sign[1:]
            print(lowest_price_with_sign)
            ebay_price_list.append(lowest_price)
        except:
            print("FAIL")
            ebay_price_list.append(999999)

    df[current_date] = ebay_price_list
    df.to_csv(file_name)


def test_check_amazon_prices_today(file_name):
    new_product_prices_list = []
    new_delivery_prices_list = []
    used_product_prices_list = []
    used_delivery_prices_list = []

    df = pd.read_csv(file_name)
    number_of_rows = df.shape[0]

    service = Service("..\chromedriver_win32")
    options = webdriver.ChromeOptions()
    # https://stackoverflow.com/questions/12211781/how-to-maximize-window-in-chrome-using-webdriver-python
    options.add_argument("--start-maximized")
    #options.add_argument("--headless=new")
    options.add_argument('--blink-settings=imagesEnabled=false')
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    for row_number in range(1):
        edition_format = df.iloc[row_number, [2]][0]
        # https://stackoverflow.com/questions/27387415/how-would-i-get-everything-before-a-in-a-string-python
        isbn = str((df.iloc[row_number,[3]])[0]).split(".")[0]
        time1 = datetime.now()
        print("Item: " + str(row_number))
        URL_raw = df.iloc[row_number, [1]]
        URL = "https://www." + URL_raw[0]
        print(URL)
        driver = webdriver.Chrome(service=service, options=options)

        # New paperback
        # https://www.amazon.co.uk/gp/offer-listing/1472223888/ref=tmm_pap_new_olp_0?ie=UTF8&amp;condition=new

        # Used paperback
        # https://www.amazon.co.uk/gp/offer-listing/1472223888/ref=tmm_pap_used_olp_0?ie=UTF8&amp;condition=used

        # New Hardcover
        # https://www.amazon.co.uk/gp/offer-listing/0786965606/ref=tmm_hrd_new_olp_0?ie=UTF8&amp;condition=new

        # Used Hardcover
        # https://www.amazon.co.uk/gp/offer-listing/0857528122/ref=tmm_hrd_used_olp_0?ie=UTF8&condition=used



        # New Products
        try:
            # if edition_format=="Paperback" or edition_format=="paperback":
            #     URL = "https://www.amazon.co.uk/gp/offer-listing/" + str(isbn) + "/ref=tmm_pap_new_olp_0?ie=UTF8&condition=new"
            # elif edition_format=="Hardcover" or edition_format=="hardcover":
            #     URL = "https://www.amazon.co.uk/gp/offer-listing/" + str(isbn) + "/ref=tmm_hrd_new_olp_0?ie=UTF8&condition=new"
            # else:
            #     URL = URL
            URL = "https://www.amazon.co.uk/dp/" + str(isbn)
            URL = "https://www.amazon.co.uk/gp/offer-listing/1472223888/ref=tmm_pap_new_olp_0?ie=UTF8&condition=new"
            print(URL)
            driver.get(URL)
            html = driver.page_source
            soup = BeautifulSoup(html, features="lxml")

            # New Product Price
            try:
                results = soup.find("span", class_="a-offscreen")
                if results is not None:
                    price = results.get_text()
                    price_without_sign = price[1:]
                    new_product_prices_list.append(price_without_sign)
                    print("New Product Price: ", price_without_sign)
                else:
                    new_product_prices_list.append(-999999)
                    print("New Product Price: FAIL")
            except Exception as e:
                print("Except: New Product price")
                print(e)

            # New Delivery Price
            try:
                results1 = soup.find("div", id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                print("New delivery price: " + results2["data-csa-c-delivery-price"])
                if (results2["data-csa-c-delivery-price"]=="FREE"):
                    new_delivery_prices_list.append(0)
                else:
                    new_delivery_prices_list.append(results2["data-csa-c-delivery-price"])
            except:
                new_delivery_prices_list.append(-999999)
                print("New Delivery Price: FAIL")

        except Exception as e:
            print("Except: Whole try-catch block for new products")
            print(e)



        # Used Products
        try:
            if edition_format=="Paperback" or edition_format=="paperback":
                URL = "https://www.amazon.co.uk/gp/offer-listing/" + str(isbn) + "/ref=tmm_pap_used_olp_0?ie=UTF8&condition=used"
            elif edition_format=="Hardcover" or edition_format=="hardcover":
                URL = "https://www.amazon.co.uk/gp/offer-listing/" + str(isbn) + "/ref=tmm_hrd_used_olp_0?ie=UTF8&condition=used"
            else:
                URL = URL
            URL = "https://www.amazon.co.uk/gp/offer-listing/1472223888/ref=tmm_pap_used_olp_0?ie=UTF8&condition=used"
            URL = "https://www.amazon.co.uk/dp/1472223888"


            # https://www.amazon.co.uk/gp/offer-listing/1472223888/ref=tmm_pap_used_olp_0?ie=UTF8&condition=used
            # https://www.amazon.co.uk/gp/offer-listing/1472223888/ref=tmm_pap_used_olp_0?ie=UTF8&condition=used
            # https://www.amazon.co.uk/gp/offer-listing/1472223888/ref=tmm_pap_new_olp_0?ie=UTF8&condition=new

            # Used Product Price
            try:
                print(URL)
                driver.get(URL)
                # Accept Cookies https://stackoverflow.com/questions/65056154/handling-accept-cookies-popup-with-selenium-in-python
                WebDriverWait(driver, 20000).until(
                    EC.element_to_be_clickable(
                        (
                        By.XPATH, "// *[ @ id = 'sp-cc-accept']"))).click()

                # https://stackoverflow.com/questions/20986631/how-can-i-scroll-a-web-page-using-selenium-webdriver-in-python
                driver.execute_script("window.scrollTo(document.body.scrollHeight, 0);")
                WebDriverWait(driver, 20000).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//*[@id='tmmSwatches']/ul/li[4]/span/span[3]/span[1]/span/a"))).click()
                WebDriverWait(driver, 20000).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//*[contains(@href, 'ref=tmm_pap_used_olp_0?ie=UTF8&condition=used')]"))).click()

                # /html/body/div[1]/div[2]/div[4]/div[1]/div[6]/div[7]/div[2]/div[2]/ul/li[4]/span/span[3]/span[1]/span/a
                # //*[@id='tmmSwatches']/ul/li[4]/span/span[3]/span[1]/span/a

                html = driver.page_source
                soup = BeautifulSoup(html, features="lxml")
                results = soup.find("span", class_="a-offscreen")
                if results is not None:
                    price = results.get_text()
                    price_without_sign = price[1:]
                    used_product_prices_list.append(price_without_sign)
                    print("Used Product Price: ", price_without_sign)
                else:
                    used_product_prices_list.append(-999999)
                    print("Used Product Price: FAIL")
            except:
                used_product_prices_list.append(-999999)
                print("Used Product Price: FAIL")

            # Used Delivery Price
            try:
                pass
            except:
                new_product_prices_list.append(999999)
                print("Used Delivery Price: FAIL")

        except:
            pass



        time2 = datetime.now()
        time_diff = time2 - time1
        print("Time: ", time_diff.seconds)
        print()

        exit(1)

        driver.quit()
    #df["New Product Price"] = new_product_prices_list
    #df["New Delivery Price"] = new_delivery_prices_list
    #df["New Total Price"] = new_product_prices_list + new_delivery_prices_list
    #df["Used Product Price"] = used_product_prices_list
    #df["Used Delivery Price"] = used_delivery_prices_list
    #df["Used Total Price"] = used_product_prices_list + used_delivery_prices_list
    #df.to_csv(file_name, index=False)







def setup_database(links,base_file_name="scraped_database_data", URL=None):

    create_blank_csv("./"+ base_file_name +"_amazon.csv", createHeader=True)

    for link in links:
        setup_list_one_page_from_amazon("./"+ base_file_name +"_amazon.csv",link)

    get_ISBN_from_list("./"+ base_file_name +"_amazon.csv")

    create_blank_csv("./" + base_file_name + "_ebay.csv")
    df = pd.read_csv("./" + base_file_name + "_amazon.csv")
    df.to_csv("./" + base_file_name + "_ebay.csv", index=False)

    check_amazon_prices_today("./" + base_file_name + "_amazon.csv")
    check_ebay_prices_today("./" + base_file_name + "_ebay.csv")



def main():
    #test_check_amazon_prices_today("./Web Scraping/BeautifulSoup/ScraperAmazonDatasetTargetedPrices.csv")
    #check_ebay_prices_today("Targeted")
    #create_blank_csv("./scraped_database_data.csv", createHeader=True)
    #setup_list_one_page_from_amazon("./scraped_database_data.csv")
    test_check_amazon_prices_today("scraped_database_data.csv")


if __name__ == "__main__":
    main()


