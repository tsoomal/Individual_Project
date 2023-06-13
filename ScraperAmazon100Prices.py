import csv
from datetime import datetime
import time
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

def setup_list_one_page(URL=None):
    service = Service(r"C:\Users\Tejinder Soomal\Downloads\chromedriver_win32")
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
        else:
            print("ERROR! Counter: ", counter)
        print(title)

        # link
        link_element = book_element.find("a", class_="a-link-normal")
        href = link_element["href"]
        link = "amazon.co.uk" + href
        print(link)

        data = [title, link]
        with open("ScraperAmazonDataset100Prices.csv", "a+", newline="", encoding="UTF8") as f:
            writer = csv.writer(f)
            writer.writerow(data)


def setup_list(URL = None):
    # Uses Amazon's Best Selling 100 Book list to setup a list of books to track
    # Book Title, Link, ISBN
    create_blank_csv("ScraperAmazonDataset100Prices.csv", createHeader=True)
    setup_list_one_page()
    setup_list_one_page("https://www.amazon.co.uk/best-sellers-books-Amazon/zgbs/books/ref=zg_bs_pg_2?_encoding=UTF8&pg=2")
    get_ISBN_from_list()

    create_blank_csv("ScraperEbayDataset100Prices.csv")
    df = pd.read_csv("ScraperAmazonDataset100Prices.csv")
    df.to_csv("ScraperEbayDataset100Prices.csv", index=False)

    create_blank_csv("ScraperAmazonDataset100Rankings.csv")
    df = pd.read_csv("ScraperAmazonDataset100Prices.csv")
    df.to_csv("ScraperAmazonDataset100Rankings.csv",index=False)


def get_ISBN_from_list():
    pd.set_option('display.max_rows', 1000)
    pd.options.display.width = 0
    df = pd.read_csv(r"C:\Users\Tejinder Soomal\Documents\Individual Project Code\ScraperAmazonDataset100Prices.csv")
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
    df.to_csv(r"C:\Users\Tejinder Soomal\Documents\Individual Project Code\ScraperAmazonDataset100Prices.csv", index=False)


def check_amazon_prices_today(URL=None):
    now = datetime.now()
    current_date = now.strftime("%d/%m/%Y")

    prices_list = []
    amazon_ranking = []

    df = pd.read_csv("ScraperAmazonDataset100Prices.csv")
    number_of_rows = df.shape[0]

    service = Service(r"C:\Users\Tejinder Soomal\Downloads\chromedriver_win32")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument('--blink-settings=imagesEnabled=false')
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    # options.add_argument("--window-size=1920,1200")
    #chrome_driver = webdriver.Chrome(service=service, options=options)

    #with chrome_driver as driver:
    for row_number in range(number_of_rows):
        time1 = datetime.now()
        print("Item: " + str(row_number))
        URL_raw = df.iloc[row_number, [1]]
        URL = "https://www." + URL_raw[0]

        print(URL)

        driver = webdriver.Chrome(service=service, options=options)
        driver.get(URL)
        html = driver.page_source
        driver.quit()


        #soup = BeautifulSoup(html, features="html.parser")
        soup = BeautifulSoup(html, features="lxml")

        # Price
        results = soup.find("span", id="price")
        if results is not None:
            price = results.get_text()
            price_without_sign = price[1:]
            prices_list.append(price_without_sign)
            print("Price: ", price_without_sign)
        else:
            prices_list.append(999999)
            print("Price: FAIL")

        # Ranking
        try:
            results = soup.find("div", id="detailBulletsWrapper_feature_div")
            details_list = results.findAll("ul", class_="a-unordered-list a-nostyle a-vertical a-spacing-none detail-bullet-list")
            selling_text = details_list[1].get_text()
            selling_text_space_delimited_list = selling_text.split()
            rank = selling_text_space_delimited_list[3]
            amazon_ranking.append(rank)
            print("Rank: ", rank)
        except:
            print("Rank: FAIL")
            amazon_ranking.append(999999)

        time2 = datetime.now()
        time_diff = time2 - time1
        print("Time: ", time_diff.seconds)
        print()


    #driver.quit()
    df[current_date] = prices_list
    df.to_csv("ScraperAmazonDataset100Prices.csv", index=False)

    df2 = pd.read_csv("ScraperAmazonDataset100Rankings.csv")
    df2[current_date] = amazon_ranking
    df2.to_csv("ScraperAmazonDataset100Rankings.csv", index=False)


def check_ebay_prices_today_selenium():
    now = datetime.now()
    current_date = now.strftime("%d/%m/%Y")

    df = pd.read_csv(r"C:\Users\Tejinder Soomal\Documents\Individual Project Code\ScraperAmazonDataset100Prices.csv")
    number_of_rows = df.shape[0]
    isbn_col = df.iloc[:, [2]]
    ebay_price_list = []

    for row_number in range(number_of_rows):
        isbn_for_row = (df.iloc[row_number, [2]])[0]

        URL = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
            isbn_for_row) + "&_sacat=0&_sop=15&LH_ItemCondition=3&LH_PrefLoc=2&rt=nc&LH_BIN=1"

        service = Service(r"C:\Users\Tejinder Soomal\Downloads\chromedriver_win32")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1200")
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(URL)
        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, features="lxml")
        results = soup.find("ul", class_="srp-results")
        books_html = results.findAll("span", class_="s-item__price")

        lowest_price = books_html[0].get_text()
        ebay_price_list.append(lowest_price)

    df[current_date] = ebay_price_list
    df.to_csv(r"C:\Users\Tejinder Soomal\Documents\Individual Project Code\ScraperEbayDataset100Prices.csv",
              index=False)


def check_ebay_prices_today():
    # MAKE SURE ISBN-10s WITHIN SOURCE CSV ARE FORMATTED WITH LEADING ZEROES INCLUDED
    now = datetime.now()
    current_date = now.strftime("%d/%m/%Y")

    df = pd.read_csv(r"C:\Users\Tejinder Soomal\Documents\Individual Project Code\ScraperEbayDataset100Prices.csv")
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
        results = soup.find("ul", class_="srp-results")
        books_html = results.findAll("span", class_="s-item__price")
        if len(books_html) == 0:
            print("FAIL")
            ebay_price_list.append(999999)
        else:
            lowest_price_with_sign = books_html[0].get_text()
            lowest_price = lowest_price_with_sign[1:]
            print(lowest_price_with_sign)
            ebay_price_list.append(lowest_price)

    # for row_count, price in enumerate(ebay_price_list):
    #     if price == 999999:
    #         isbn_for_row = (df.iloc[row_count, [2]])[0]
    #
    #         URL = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
    #             isbn_for_row) + "&_sacat=0&_sop=15&LH_ItemCondition=3&LH_PrefLoc=2&rt=nc&LH_BIN=1"
    #
    #         service = Service(r"C:\Users\Tejinder Soomal\Downloads\chromedriver_win32")
    #         options = webdriver.ChromeOptions()
    #         options.add_argument("--headless=new")
    #         options.add_argument("--window-size=1920,1200")
    #         driver = webdriver.Chrome(service=service, options=options)
    #         driver.get(URL)
    #         html = driver.page_source
    #         driver.quit()
    #
    #         soup = BeautifulSoup(html, features="html.parser")
    #         results = soup.find("ul", class_="srp-results")
    #         books_html = results.findAll("span", class_="s-item__price")
    #
    #         if len(books_html) == 0:
    #             ebay_price_list.append(999999)
    #             print(URL)
    #             print("FAIL")
    #         else:
    #             lowest_price_with_sign = books_html[0].get_text()
    #             lowest_price = lowest_price_with_sign[1:]
    #             print(URL)
    #             print("SLOW")
    #             print(lowest_price_with_sign)
    #             ebay_price_list[row_number] = lowest_price

    df[current_date] = ebay_price_list
    df.to_csv(r"C:\Users\Tejinder Soomal\Documents\Individual Project Code\ScraperEbayDataset100Prices.csv", index=False)

def create_blank_csv(file_name, createHeader=False):
    if createHeader==True:
        header = ["Title", "Link"]
        with open(file_name, "w", newline="", encoding="UTF8") as f:
           writer = csv.writer(f)
           writer.writerow(header)
    else:
        with open(file_name, "w", newline="", encoding="UTF8") as f:
           writer = csv.writer(f)



def get_all_best_seller_books_links(URL = None):
    service = Service(r"C:\Users\Tejinder Soomal\Downloads\chromedriver_win32")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1200")
    driver = webdriver.Chrome(service=service, options=options)
    if URL == None:
        URL = "https://www.amazon.co.uk/gp/bestsellers/books"
    driver.get(URL)

    # Accept Cookies
    wait = WebDriverWait(driver, 10)
    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sp-cc-accept"]')))
    driver.find_element("xpath", '//*[@id="sp-cc-accept"]').click()

    scroll_to_bottom(driver)
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, features="lxml")
    results_raw = soup.findAll("div", class_="_p13n-zg-nav-tree-all_style_zg-browse-group__88fbz")
    results = results_raw[0]
    links_list_raw = results.find_all("a", href=True)

    links_list = []

    for link in links_list_raw:
        print ("https://www.amazon.co.uk" + link["href"])
        links_list.append("https://www.amazon.co.uk" + link["href"])
    print()

    return links_list


def get_all_best_seller_books(second_tranche = False):

    base_links_list = []

    if second_tranche == False:
        base_links_list = get_all_best_seller_books_links()

        for URL in base_links_list:
            print(URL)

            # list = ["https://www.amazon.co.uk/Best-Sellers-Books-Society-Politics-Philosophy/zgbs/books/60/ref=zg_bs_nav_books_1",
            #         "https://www.amazon.co.uk/Best-Sellers-Books-Sports-Hobbies-Games/zgbs/books/55/ref=zg_bs_nav_books_1",
            #         "https://www.amazon.co.uk/Best-Sellers-Books-Travel-Tourism/zgbs/books/83/ref=zg_bs_nav_books_1",
            #         "https://www.amazon.co.uk/Best-Sellers-Books-University-Textbooks/zgbs/books/14909553031/ref=zg_bs_nav_books_1",
            #         "https://www.amazon.co.uk/Best-Sellers-Books-Teen-Young-Adult/zgbs/books/52/ref=zg_bs_nav_books_1"]
            #
            # if URL not in list:
            #     continue

            URL1 = URL
            URL2 = URL[:-21] + "ref=zg_bs_pg_2?_encoding=UTF8&pg=2"
            setup_list_one_page(URL1)
            setup_list_one_page(URL2)

    elif second_tranche == True:
        # Get bestseller lists of sub-topics within topics.
        base_links_list2 = get_all_best_seller_books_links()
        skip_links = ["https://www.amazon.co.uk/Best-Sellers-Books-Arts-Photography/zgbs/books/91/ref=zg_bs_nav_books_1",
                      "https://www.amazon.co.uk/Best-Sellers-Books-Biographies-Memoirs/zgbs/books/67/ref=zg_bs_nav_books_1",
                      "https://www.amazon.co.uk/Best-Sellers-Books-Business-Finance-Law/zgbs/books/68/ref=zg_bs_nav_books_1",
                      "https://www.amazon.co.uk/Best-Sellers-Books-Calendars-Diaries-Annuals/zgbs/books/507848/ref=zg_bs_nav_books_1",
                      "https://www.amazon.co.uk/Best-Sellers-Books-Erotica/zgbs/books/9587997031/ref=zg_bs_nav_books_1",
                      "https://www.amazon.co.uk/Best-Sellers-Books-Comics-Graphic-Novels/zgbs/books/274081/ref=zg_bs_nav_books_1",
                      "https://www.amazon.co.uk/Best-Sellers-Books-Computing-Internet/zgbs/books/71/ref=zg_bs_nav_books_1",
                      "https://www.amazon.co.uk/Best-Sellers-Books-Crime-Thrillers-Mystery/zgbs/books/72/ref=zg_bs_nav_books_1",
                      "https://www.amazon.co.uk/Best-Sellers-Books-Education-Studies-Teaching-Resources/zgbs/books/496792/ref=zg_bs_nav_books_1",
                      "https://www.amazon.co.uk/Best-Sellers-Books-Literature-Fiction/zgbs/books/62/ref=zg_bs_nav_books_1",
                      "https://www.amazon.co.uk/Best-Sellers-Books-Food-Drink/zgbs/books/66/ref=zg_bs_nav_books_1",
                      "https://www.amazon.co.uk/Best-Sellers-Books-Health-Family-Lifestyle/zgbs/books/74/ref=zg_bs_nav_books_1",]
        for URL in base_links_list2:
            if URL in skip_links:
                print(URL)
                print("PASS")
                continue
            print(URL)
            base_links_list = get_all_best_seller_books_links(URL)
            for URL21 in base_links_list:
                if URL == "https://www.amazon.co.uk/best-sellers-books-Amazon/zgbs/books/ref=zg_bs_unv_books_1_91_1":
                    print("PASS")
                    pass

                print(URL21)
                setup_list_one_page(URL21)

                # Find URL22. i.e. second page of bestsellers
                last_slash_index = URL21.rfind("/")
                second_last_slash_index = URL21[:last_slash_index].rfind("/")
                search_ID = URL21[second_last_slash_index + 1:last_slash_index]
                URL22 = "https://www.amazon.co.uk/best-sellers-books-Amazon/zgbs/books/" + search_ID + "/ref=zg_bs_pg_2?_encoding=UTF8&pg=2"

                print(URL22)
                setup_list_one_page(URL22)

    get_ISBN_from_list()
    remove_duplicate_rows()
    delete_invalid_ISBN()


def remove_duplicate_rows():
    df = pd.read_csv(r"C:\Users\Tejinder Soomal\Documents\Individual Project Code\ScraperAmazonDataset100Prices.csv")
    df.drop_duplicates(subset=["ISBN"], inplace=True, keep='first')
    df.to_csv(r"C:\Users\Tejinder Soomal\Documents\Individual Project Code\ScraperAmazonDataset100Prices.csv",
              index=False)

def delete_invalid_ISBN():
    df = pd.read_csv(r"C:\Users\Tejinder Soomal\Documents\Individual Project Code\ScraperAmazonDataset100Prices.csv")
    ISBN_column = df.iloc[:, [2]]
    number_of_rows = df.shape[0]
    rows_to_delete = []

    for row_number in range(number_of_rows):
        ISBN_chosen_row = df.iloc[row_number, [2]]
        ISBN_chosen = ISBN_chosen_row[0]
        print(ISBN_chosen)
        for char in ISBN_chosen:
            if char.isnumeric() or char == "x" or char == "X":
                pass
            else:
                print("CHAR: " + char)
                rows_to_delete.append(row_number)
                break

    if len(rows_to_delete) != 0:
        for row in rows_to_delete:
            df = df.drop(row)

    df.to_csv(r"C:\Users\Tejinder Soomal\Documents\Individual Project Code\ScraperAmazonDataset100Prices.csv",
              index=False)

def main():
    #  while(True):
    #     check_prices()
    #     df = pd.read_csv(r"C:\Users\Tejinder Soomal\Documents\Individual Project Code\ScraperIndeedDataset.csv")
    #     print(df)
    #     time.sleep(86400)

    #create_blank_csv("ScraperEbayDataset100Prices.csv", createHeader=True)
    #setup_list()
    #setup_list_one_page("https://www.amazon.co.uk/Best-Sellers-Books-Business-Finance-Law/zgbs/books/68/ref=zg_bs_nav_books_1")

    #get_all_best_seller_books(second_tranche=True)

    #get_ISBN_from_list()
    #remove_duplicate_rows()
    #delete_invalid_ISBN()

    check_amazon_prices_today()
    #check_ebay_prices_today()

    # pd.set_option('display.max_rows', 1000)
    # pd.set_option('display.max_columns', 1000)
    # pd.set_option('display.width', 1000)
    # df = pd.read_csv(r"C:\Users\Tejinder Soomal\Documents\Individual Project Code\ScraperAmazonDataset100Prices.csv")
    # print (df)



if __name__ == "__main__":
    main()


