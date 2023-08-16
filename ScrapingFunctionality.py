import csv
import os
from datetime import datetime
import time
import re
import werkzeug

#from app import Amazon, db, Ebay
# https://stackoverflow.com/questions/7336802/how-to-avoid-circular-imports-in-python
import app

from sqlalchemy.exc import IntegrityError
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
        span_element = book_element.findAll("div", class_="_cDEzb_p13n-sc-css-line-clamp-2_EWgCb")
        # author = span_element[1].get_text()
        if not span_element:
            print("IF STATEMENT")
            span_element = book_element.findAll("div", class_="_cDEzb_p13n-sc-css-line-clamp-1_1Fn1y")
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
        link = "https://www.amazon.co.uk" + href
        print(link)

        # Edition Format
        try:
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
        except:
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
        link_in_row = df.iloc[row_number,[1]]
        string_row = link_in_row[0]
        index_of_dp = string_row.find("dp/")
        rest_of_string = string_row[(index_of_dp+3):]
        isbn_number = rest_of_string[:10]
        isbn_list.append(isbn_number)

    df["ISBN"] = isbn_list
    df.to_csv(file_name, index=False)

    # Remove Duplicate Rows
    df = pd.read_csv(file_name)
    df.drop_duplicates(subset=["ISBN"], inplace=True, keep='first')
    df.to_csv(file_name, index=False)

    # Delete alleged ISBNs not in ISBN format
    df = pd.read_csv(file_name)
    ISBN_column = df.iloc[:, [3]]
    number_of_rows = df.shape[0]
    rows_to_delete = []

    for row_number in range(number_of_rows):
        ISBN_chosen_row = df.iloc[row_number, [3]]
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

    df.to_csv(file_name,
              index=False)


def check_ebay_prices_today(file_name, only_create_new_books=False):
    now = datetime.now()

    df = pd.read_csv(file_name)
    number_of_rows = df.shape[0]
    isbn_col = df.iloc[:, [4]]

    for row_number in range(number_of_rows):
        book_name = df.iloc[row_number, [0]][0]
        new_ebay_link = df.iloc[row_number, [1]][0]
        used_ebay_link = df.iloc[row_number, [2]][0]
        edition_format = df.iloc[row_number, [3]][0]
        # https://stackoverflow.com/questions/27387415/how-would-i-get-everything-before-a-in-a-string-python
        isbn = str((df.iloc[row_number,[4]])[0]).split(".")[0]
        isbn = isbn.zfill(10)

        if only_create_new_books==True:
            try:
                book_in_ebay_db = app.Ebay.query.get_or_404(isbn)
                print(row_number)
                print(book_in_ebay_db)
                if book_in_ebay_db.new_product_price==-999 and book_in_ebay_db.new_delivery_price==-999 and \
                        book_in_ebay_db.new_total_price==-999 and book_in_ebay_db.used_product_price==-999 and \
                        book_in_ebay_db.used_delivery_price==-999 and book_in_ebay_db.used_total_price==-999:
                    try:
                        app.db.session.delete(book_in_ebay_db)
                        app.db.session.commit()
                    except:
                        app.db.session.rollback()
                else:
                    continue
            except werkzeug.exceptions.NotFound:
                pass

        time1 = datetime.now()
        print("Item: " + str(row_number+1))
        print(book_name)
        print(edition_format)

        # New Products
        try:
            URL = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
                isbn) + "&_sacat=0&_sop=15&LH_ItemCondition=3&LH_PrefLoc=2&rt=nc&LH_BIN=1"
            print(URL)
            page = requests.get(URL)
            html = page.text
            soup = BeautifulSoup(html, features="lxml")

            # New Product Price
            try:
                results = soup.find("ul", class_="srp-results")
                new_product_price_list = results.findAll("span", class_="s-item__price")
                new_product_price_with_sign = new_product_price_list[0].get_text()
                new_product_price = new_product_price_with_sign[1:]
                print("New Product Price: £" + new_product_price)
            except Exception as e:
                new_product_price = -999
                print("New Product Price: FAIL")

            # New Delivery Price
            try:
                results = soup.find("ul", class_="srp-results")
                new_delivery_price_list = results.findAll("span", class_="s-item__shipping s-item__logisticsCost")
                new_delivery_price_with_sign = new_delivery_price_list[0].get_text()
                if (("Free" in new_delivery_price_with_sign) or ("free" in new_delivery_price_with_sign)) and (("Postage" in new_delivery_price_with_sign) or ("postage" in new_delivery_price_with_sign)):
                    new_delivery_price = 0
                    print("New Delivery Price: £0.00")
                else:
                    #new_delivery_price = new_delivery_price_with_sign[1:]
                    new_delivery_price = re.findall("\d+\.\d+",new_delivery_price_with_sign)[0]
                    print("New Delivery Price: £" + new_delivery_price)
            except:
                try:
                    results = soup.find("ul", class_="srp-results")
                    new_delivery_price_list = results.findAll("span", class_="s-item__dynamic s-item__freeXDays")
                    new_delivery_price_with_sign = new_delivery_price_list[0].get_text()
                    if (("Free" in new_delivery_price_with_sign) or ("free" in new_delivery_price_with_sign)) and (
                            ("Postage" in new_delivery_price_with_sign) or ("postage" in new_delivery_price_with_sign)):
                        new_delivery_price = 0
                        print("New Delivery Price: £0.00")
                    else:
                        # https://www.tutorialspoint.com/Extract-decimal-numbers-from-a-string-in-Python#:~:text=To%20extract%20decimal%20numbers%20from,to%20work%20with%20regular%20expressions.
                        new_delivery_price = re.findall("\d+\.\d+", new_delivery_price_with_sign)[0]
                        print("New Delivery Price: £" + new_delivery_price)
                except Exception as e:
                    new_delivery_price = -999
                    print("New Delivery Price: FAIL")

        except Exception as e:
            print("Except: Whole try-catch block for new products")
            print(e)


        # Used Products
        try:
            URL = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
                isbn) + "&_sacat=0&_sop=15&LH_BIN=1&LH_PrefLoc=1&rt=nc&LH_ItemCondition=4"
            print(URL)
            page = requests.get(URL)
            html = page.text
            soup = BeautifulSoup(html, features="lxml")

            # Used Product Price
            try:
                results = soup.find("ul", class_="srp-results")
                used_product_price_list = results.findAll("span", class_="s-item__price")
                used_product_price_with_sign = used_product_price_list[0].get_text()
                used_product_price = used_product_price_with_sign[1:]
                print("Used Product Price: £" + used_product_price)
            except Exception as e:
                used_product_price = -999
                print("Used Product Price: FAIL")

            # Used Delivery Price
            try:
                results = soup.find("ul", class_="srp-results")
                used_delivery_price_list = results.findAll("span", class_="s-item__shipping s-item__logisticsCost")
                used_delivery_price_with_sign = used_delivery_price_list[0].get_text()
                if (("Free" in used_delivery_price_with_sign) or ("free" in used_delivery_price_with_sign)) and (
                        ("Postage" in used_delivery_price_with_sign) or ("postage" in used_delivery_price_with_sign)):
                    used_delivery_price = 0
                    print("Used Delivery Price: £0.00")
                else:
                    used_delivery_price = re.findall("\d+\.\d+",used_delivery_price_with_sign)[0]
                    print("Used Delivery Price: £" + used_delivery_price)
            except:
                try:
                    results = soup.find("ul", class_="srp-results")
                    used_delivery_price_list = results.findAll("span", class_="s-item__dynamic s-item__freeXDays")
                    used_delivery_price_with_sign = used_delivery_price_list[0].get_text()
                    if (("Free" in used_delivery_price_with_sign) or ("free" in used_delivery_price_with_sign)) and (
                            ("Postage" in used_delivery_price_with_sign) or (
                            "postage" in used_delivery_price_with_sign)):
                        used_delivery_price = 0
                        print("Used Delivery Price: £0.00")
                    else:
                        # https://www.tutorialspoint.com/Extract-decimal-numbers-from-a-string-in-Python#:~:text=To%20extract%20decimal%20numbers%20from,to%20work%20with%20regular%20expressions.
                        used_delivery_price = re.findall("\d+\.\d+", used_delivery_price_with_sign)[0]
                        print("Used Delivery Price: £" + used_delivery_price)
                except Exception as e:
                    used_delivery_price = -999
                    print("Used Delivery Price: FAIL")

        except Exception as e:
            print("Except: Whole try-catch block for used products")
            print(e)

        time2 = datetime.now()
        time_diff = time2 - time1
        print("Time: ", time_diff.seconds)

        try:
            new_total_price_raw = float(new_product_price) + float(new_delivery_price)
        except:
            new_product_price=-999
            new_delivery_price=-999
            new_total_price_raw=-999

        if new_total_price_raw <= -1000 or new_total_price_raw >= 1000:
            new_total_price_raw = -999

        try:
            used_total_price_raw = float(used_product_price)+float(used_delivery_price)
        except:
            used_product_price = -999
            used_delivery_price = -999
            used_total_price_raw = -999
        if used_total_price_raw <= -1000 or used_total_price_raw >= 1000:
            used_total_price_raw = -999


        try:
            historical_new_total_price = get_ebay_historical_price(isbn, "new")
            historical_used_total_price = get_ebay_historical_price(isbn, "used")
            new_book = app.Ebay(book_name=book_name, new_ebay_link=new_ebay_link, used_ebay_link=used_ebay_link,
                                isbn=isbn, edition_format=edition_format,
                                new_product_price=[new_product_price], new_delivery_price=[new_delivery_price],
                                new_total_price=[new_total_price_raw],
                                historical_new_total_price=[historical_new_total_price],
                                used_product_price=[used_product_price], used_delivery_price=[used_delivery_price],
                                used_total_price=[used_total_price_raw],
                                historical_used_total_price=[historical_used_total_price])
            app.db.session.add(new_book)
            app.db.session.commit()
            print("Book added to Ebay table in db.")
            print()

        except IntegrityError:
            app.db.session.rollback()
            try:
                book_to_append_ebay = app.Ebay.query.get_or_404(isbn)

                # If previous price was found, but not found now, then it means that the book must have sold recently.
                # Price is set at the last known price.
                try:
                    if float(new_total_price_raw)==-999 and book_to_append_ebay.new_total_price[-1]!=-999:
                        new_product_price = book_to_append_ebay.new_product_price[-1]
                        new_delivery_price = book_to_append_ebay.new_delivery_price[-1]
                        new_total_price_raw = book_to_append_ebay.new_total_price[-1]
                        print("NEW: IDENTIFIED SOLD BOOK PREVIOUSLY. COPYING PREVIOUS PRICE.")

                    if float(used_total_price_raw) == -999 and book_to_append_ebay.used_total_price[-1] != -999:
                        used_product_price = book_to_append_ebay.used_product_price[-1]
                        used_delivery_price = book_to_append_ebay.used_delivery_price[-1]
                        used_total_price_raw = book_to_append_ebay.used_total_price[-1]
                        print("USED: IDENTIFIED SOLD BOOK PREVIOUSLY. COPYING PREVIOUS PRICE.")
                except Exception as e:
                    print("ERROR: Failed to set price at last known price, despite price not found now.")
                    print(e)

                book_to_append_ebay.new_product_price = book_to_append_ebay.new_product_price + [new_product_price]
                book_to_append_ebay.new_delivery_price = book_to_append_ebay.new_delivery_price + [new_delivery_price]
                book_to_append_ebay.new_total_price = book_to_append_ebay.new_total_price + [new_total_price_raw]
                book_to_append_ebay.historical_new_total_price = book_to_append_ebay.historical_new_total_price + [historical_new_total_price]
                book_to_append_ebay.used_product_price = book_to_append_ebay.used_product_price + [used_product_price]
                book_to_append_ebay.used_delivery_price = book_to_append_ebay.used_delivery_price + [used_delivery_price]
                book_to_append_ebay.used_total_price = book_to_append_ebay.used_total_price + [used_total_price_raw]
                book_to_append_ebay.historical_used_total_price = book_to_append_ebay.historical_used_total_price + [historical_used_total_price]
                app.db.session.commit()
                print("Book updated in Ebay table in db.")
                print()
            except:
                app.db.session.rollback()
        except:
            app.db.session.rollback()


def check_ebay_prices_today_isbn(isbn):

    isbn = isbn.zfill(10)

    time1 = datetime.now()

    # New Products
    try:
        URL = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
            isbn) + "&_sacat=0&_sop=15&LH_ItemCondition=3&LH_PrefLoc=2&rt=nc&LH_BIN=1"
        print(URL)
        page = requests.get(URL)
        html = page.text
        soup = BeautifulSoup(html, features="lxml")

        # New Product Price
        try:
            results = soup.find("ul", class_="srp-results")
            new_product_price_list = results.findAll("span", class_="s-item__price")
            new_product_price_with_sign = new_product_price_list[0].get_text()
            new_product_price = new_product_price_with_sign[1:]
            print("New Product Price: £" + new_product_price)
        except Exception as e:
            new_product_price = -999
            print("New Product Price: FAIL")

        # New Delivery Price
        try:
            results = soup.find("ul", class_="srp-results")
            new_delivery_price_list = results.findAll("span", class_="s-item__shipping s-item__logisticsCost")
            new_delivery_price_with_sign = new_delivery_price_list[0].get_text()
            if (("Free" in new_delivery_price_with_sign) or ("free" in new_delivery_price_with_sign)) and (("Postage" in new_delivery_price_with_sign) or ("postage" in new_delivery_price_with_sign)):
                new_delivery_price = 0
                print("New Delivery Price: £0.00")
            else:
                #new_delivery_price = new_delivery_price_with_sign[1:]
                new_delivery_price = re.findall("\d+\.\d+",new_delivery_price_with_sign)[0]
                print("New Delivery Price: £" + new_delivery_price)
        except:
            try:
                results = soup.find("ul", class_="srp-results")
                new_delivery_price_list = results.findAll("span", class_="s-item__dynamic s-item__freeXDays")
                new_delivery_price_with_sign = new_delivery_price_list[0].get_text()
                if (("Free" in new_delivery_price_with_sign) or ("free" in new_delivery_price_with_sign)) and (
                        ("Postage" in new_delivery_price_with_sign) or ("postage" in new_delivery_price_with_sign)):
                    new_delivery_price = 0
                    print("New Delivery Price: £0.00")
                else:
                    # https://www.tutorialspoint.com/Extract-decimal-numbers-from-a-string-in-Python#:~:text=To%20extract%20decimal%20numbers%20from,to%20work%20with%20regular%20expressions.
                    new_delivery_price = re.findall("\d+\.\d+", new_delivery_price_with_sign)[0]
                    print("New Delivery Price: £" + new_delivery_price)
            except Exception as e:
                new_delivery_price = -999
                print("New Delivery Price: FAIL")

    except Exception as e:
        print("Except: Whole try-catch block for new products")
        print(e)


    # Used Products
    try:
        URL = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
            isbn) + "&_sacat=0&_sop=15&LH_BIN=1&LH_PrefLoc=1&rt=nc&LH_ItemCondition=4"
        print(URL)
        page = requests.get(URL)
        html = page.text
        soup = BeautifulSoup(html, features="lxml")

        # Used Product Price
        try:
            results = soup.find("ul", class_="srp-results")
            used_product_price_list = results.findAll("span", class_="s-item__price")
            used_product_price_with_sign = used_product_price_list[0].get_text()
            used_product_price = used_product_price_with_sign[1:]
            print("Used Product Price: £" + used_product_price)
        except Exception as e:
            used_product_price = -999
            print("Used Product Price: FAIL")

        # Used Delivery Price
        try:
            results = soup.find("ul", class_="srp-results")
            used_delivery_price_list = results.findAll("span", class_="s-item__shipping s-item__logisticsCost")
            used_delivery_price_with_sign = used_delivery_price_list[0].get_text()
            if (("Free" in used_delivery_price_with_sign) or ("free" in used_delivery_price_with_sign)) and (
                    ("Postage" in used_delivery_price_with_sign) or ("postage" in used_delivery_price_with_sign)):
                used_delivery_price = 0
                print("Used Delivery Price: £0.00")
            else:
                used_delivery_price = re.findall("\d+\.\d+",used_delivery_price_with_sign)[0]
                print("Used Delivery Price: £" + used_delivery_price)
        except:
            try:
                results = soup.find("ul", class_="srp-results")
                used_delivery_price_list = results.findAll("span", class_="s-item__dynamic s-item__freeXDays")
                used_delivery_price_with_sign = used_delivery_price_list[0].get_text()
                if (("Free" in used_delivery_price_with_sign) or ("free" in used_delivery_price_with_sign)) and (
                        ("Postage" in used_delivery_price_with_sign) or (
                        "postage" in used_delivery_price_with_sign)):
                    used_delivery_price = 0
                    print("Used Delivery Price: £0.00")
                else:
                    # https://www.tutorialspoint.com/Extract-decimal-numbers-from-a-string-in-Python#:~:text=To%20extract%20decimal%20numbers%20from,to%20work%20with%20regular%20expressions.
                    used_delivery_price = re.findall("\d+\.\d+", used_delivery_price_with_sign)[0]
                    print("Used Delivery Price: £" + used_delivery_price)
            except Exception as e:
                used_delivery_price = -999
                print("Used Delivery Price: FAIL")

    except Exception as e:
        print("Except: Whole try-catch block for used products")
        print(e)

    time2 = datetime.now()
    time_diff = time2 - time1
    print("Time: ", time_diff.seconds)

    try:
        new_total_price_raw = float(new_product_price) + float(new_delivery_price)
    except:
        new_product_price=-999
        new_delivery_price=-999
        new_total_price_raw=-999

    if new_total_price_raw <= -1000 or new_total_price_raw >= 1000:
        new_total_price_raw = -999

    try:
        used_total_price_raw = float(used_product_price)+float(used_delivery_price)
    except:
        used_product_price = -999
        used_delivery_price = -999
        used_total_price_raw = -999
    if used_total_price_raw <= -1000 or used_total_price_raw >= 1000:
        used_total_price_raw = -999

    historical_new_total_price = get_ebay_historical_price(isbn, "new")
    historical_used_total_price = get_ebay_historical_price(isbn, "used")
    try:
        book_to_append_ebay = app.Ebay.query.get_or_404(isbn)

        # If previous price was found, but not found now, then it means that the book must have sold recently.
        # Price is set at the last known price.
        try:
            if float(new_total_price_raw)==-999 and book_to_append_ebay.new_total_price[-1]!=-999:
                new_product_price = book_to_append_ebay.new_product_price[-1]
                new_delivery_price = book_to_append_ebay.new_delivery_price[-1]
                new_total_price_raw = book_to_append_ebay.new_total_price[-1]
                print("NEW: IDENTIFIED SOLD BOOK PREVIOUSLY. COPYING PREVIOUS PRICE.")

            if float(used_total_price_raw) == -999 and book_to_append_ebay.used_total_price[-1] != -999:
                used_product_price = book_to_append_ebay.used_product_price[-1]
                used_delivery_price = book_to_append_ebay.used_delivery_price[-1]
                used_total_price_raw = book_to_append_ebay.used_total_price[-1]
                print("USED: IDENTIFIED SOLD BOOK PREVIOUSLY. COPYING PREVIOUS PRICE.")
        except Exception as e:
            print("ERROR: Failed to set price at last known price, despite price not found now.")
            print(e)

        book_to_append_ebay.new_product_price = book_to_append_ebay.new_product_price + [new_product_price]
        book_to_append_ebay.new_delivery_price = book_to_append_ebay.new_delivery_price + [new_delivery_price]
        book_to_append_ebay.new_total_price = book_to_append_ebay.new_total_price + [new_total_price_raw]
        book_to_append_ebay.historical_new_total_price = book_to_append_ebay.historical_new_total_price + [historical_new_total_price]
        book_to_append_ebay.used_product_price = book_to_append_ebay.used_product_price + [used_product_price]
        book_to_append_ebay.used_delivery_price = book_to_append_ebay.used_delivery_price + [used_delivery_price]
        book_to_append_ebay.used_total_price = book_to_append_ebay.used_total_price + [used_total_price_raw]
        book_to_append_ebay.historical_used_total_price = book_to_append_ebay.historical_used_total_price + [historical_used_total_price]
        app.db.session.commit()
        print("Book updated in Ebay table in db.")
        print()
    except:
        app.db.session.rollback()




def check_amazon_prices_today(file_name, only_create_new_books=False):

    df = pd.read_csv(file_name)
    number_of_rows = df.shape[0]

    # https://www.andressevilla.com/running-chromedriver-with-python-selenium-on-heroku/
    service = Service(os.environ.get("CHROMEDRIVER_PATH"))
    options = webdriver.ChromeOptions()

    # Settings Needed for Heroku
    options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    # https://stackoverflow.com/questions/12211781/how-to-maximize-window-in-chrome-using-webdriver-python
    #options.add_argument("--start-maximized")
    # https://stackoverflow.com/questions/11613869/how-to-disable-logging-using-selenium-with-python-binding
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless=new")
    options.add_argument('--blink-settings=imagesEnabled=false')
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    for row_number in range(number_of_rows):
        book_name = df.iloc[row_number, [0]][0]
        amazon_link = df.iloc[row_number, [1]][0]
        edition_format = df.iloc[row_number, [2]][0]
        # https://stackoverflow.com/questions/27387415/how-would-i-get-everything-before-a-in-a-string-python
        isbn = str((df.iloc[row_number,[3]])[0]).split(".")[0]
        isbn = isbn.zfill(10)

        if only_create_new_books==True:
            try:
                book_in_amazon_db = app.Amazon.query.get_or_404(isbn)
                print(row_number + 1)
                print(book_in_amazon_db)
                if book_in_amazon_db.new_product_price[-1]==-999 and book_in_amazon_db.new_delivery_price[-1]==-999 and \
                        book_in_amazon_db.new_total_price[-1]==-999 and book_in_amazon_db.used_product_price[-1]==-999 and \
                        book_in_amazon_db.used_delivery_price[-1]==-999 and book_in_amazon_db.used_total_price[-1]==-999:
                    app.db.session.delete(book_in_amazon_db)
                    try:
                        app.db.session.commit()
                    except:
                        app.db.session.rollback()
                else:
                    continue
            except werkzeug.exceptions.NotFound:
                pass


        time1 = datetime.now()
        print("Item: " + str(row_number+1))
        URL_raw = df.iloc[row_number, [1]]
        URL = "https://www." + URL_raw[0]
        print(book_name)
        print(amazon_link)
        print(edition_format)
        print(URL)

        try:
            driver = webdriver.Chrome(service=service, options=options)
        except:
            print("Error with Selenium.")
            try:
                driver.quit()
            except:
                return
            return

        # NEW PRODUCTS
        # NEW PRODUCT PRICES AND NEW DELIVERY PRICES
        try:
            URL = "https://www.amazon.co.uk/dp/" + str(isbn)
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
                    new_product_price = price_without_sign
                    if "age" in new_product_price:
                        html = driver.page_source
                        soup = BeautifulSoup(html, features="lxml")
                        results = soup.find("div", id="aod-offer")
                        price_text = results.find("span", class_="a-offscreen").get_text()

                        if results is not None:
                            price_without_sign = price_text[1:]
                            new_product_price = price_without_sign
                            print("New Product Price: £" + str(price_without_sign))
                        else:
                            new_product_price = -999
                            print("New Product Price: FAIL")
                    elif "%" in new_product_price:
                        # Used product on buy-box. New price definitely exists. Used price may not exist.
                        try:
                            # Click on link for new items.
                            click_new_link(driver, soup)
                            html = driver.page_source
                            soup = BeautifulSoup(html, features="lxml")
                            # New Product Price
                            results = soup.find("div",
                                                class_="a-section a-spacing-none a-padding-base aod-information-block aod-clear-float")
                            price_text = results.find("span", class_="a-offscreen").get_text()
                            new_product_price = price_text[1:]
                            print("New Product Price: " + str(new_product_price))

                            # New Delivery Price
                            results2 = results.find("span", attrs={'data-csa-c-delivery-price': True})
                            if (results2["data-csa-c-delivery-price"] == "FREE"):
                                print("New Delivery Price: " + results2["data-csa-c-delivery-price"])
                                new_delivery_price = 0
                            else:
                                delivery_price_without_sign = results2["data-csa-c-delivery-price"][1:]
                                print("New Delivery Price: £" + delivery_price_without_sign)
                                new_delivery_price = delivery_price_without_sign

                            # Go back to main product listing page.
                            driver.get(URL)
                            html = driver.page_source
                            soup = BeautifulSoup(html, features="lxml")

                            # Get Used prices
                            try:
                                # Click Used link
                                click_used_link(driver, soup)

                                html = driver.page_source
                                soup = BeautifulSoup(html, features="lxml")
                                results = soup.find("div",
                                                    class_="a-section a-spacing-none asin-container-padding aod-clear-float")
                                # Used Product Price
                                price_text = results.find("span", class_="a-offscreen").get_text()
                                used_product_price = price_text[1:]

                                results1 = results.find("div",
                                                        id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                                results2 = results1.find("span",
                                                         attrs={'data-csa-c-delivery-price': True})
                                print("New delivery price: " + results2["data-csa-c-delivery-price"])
                                if (results2["data-csa-c-delivery-price"] == "FREE"):
                                    new_delivery_price = 0
                                else:
                                    try:
                                        if "£" in results2["data-csa-c-delivery-price"]:
                                            new_delivery_price = \
                                                re.findall("\d+\.\d+",
                                                           results2["data-csa-c-delivery-price"])[0]
                                            new_delivery_price = float(new_delivery_price)
                                        else:
                                            new_delivery_price = float(
                                                results2["data-csa-c-delivery-price"])
                                    except:
                                        # new_product_price isn't a string
                                        new_delivery_price = float(
                                            results2["data-csa-c-delivery-price"])
                            except:
                                used_product_price = -999
                                used_delivery_price = -999
                        except Exception as e:
                            print("% Handler failed.")
                            new_product_price = -999
                            new_delivery_price = -999
                            used_product_price = -999
                            used_delivery_price = -999
                            print(e)

                        end_of_item_loop(amazon_link, book_name, driver, edition_format, isbn, new_delivery_price,
                                         new_product_price, time1, used_delivery_price, used_product_price)
                        continue
                    else:
                        print("New Product Price: £" + str(price_without_sign))
                else:
                    new_product_price = -999
                    print("New Product Price: FAIL")

                # New Delivery Price
                try:
                    results1 = soup.find("div", id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                    results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                    print("New delivery price: " + results2["data-csa-c-delivery-price"])
                    if (results2["data-csa-c-delivery-price"] == "FREE"):
                        new_delivery_price = 0
                    else:
                        try:
                            if "£" in results2["data-csa-c-delivery-price"]:
                                new_delivery_price = re.findall("\d+\.\d+", results2["data-csa-c-delivery-price"])[
                                    0]
                                new_delivery_price = float(new_delivery_price)
                            else:
                                new_delivery_price = float(results2["data-csa-c-delivery-price"])
                        except:
                            # new_product_price isn't a string
                            new_delivery_price = float(results2["data-csa-c-delivery-price"])

                except Exception as e:
                    # Secondary method of finding new delivery price
                    # https://www.amazon.co.uk/dp/0786968982
                    try:
                        results1 = soup.find("div", id="mir-layout-DELIVERY_BLOCK-slot-NO_PROMISE_UPSELL_MESSAGE")
                        results2 = results1.get_text()
                        if ("FREE" in results2) or ("free" in results2) or ("Free" in results2):
                            new_delivery_price = 0
                            print("New Delivery Price: £0.00")
                        else:
                            new_delivery_price = re.findall("\d+\.\d+", results2)[0]
                            print("New Delivery Price: £" + str(new_delivery_price))
                    except Exception as e:
                        # Tertiary method of finding new delivery price
                        # https://www.amazon.co.uk/dp/0786967439
                        try:
                            results1 = soup.find("div", id="delivery-block-ags-dcp-container_0")
                            results2 = results1.get_text()
                            print(results2)
                            if ("FREE delivery" in results2):
                                new_delivery_price = 0
                                print("New Delivery Price: £0.00")
                            else:
                                new_delivery_price = re.findall("\d+\.\d+", results2)[0]
                                print("New Delivery Price: £" + str(new_delivery_price))
                        except Exception as e:
                            new_delivery_price = -999
                            print("New Delivery Price: FAIL")

                # USED PRODUCTS
                # Normal method of finding used product and delivery prices
                try:
                    URL = "https://www.amazon.co.uk/dp/" + str(isbn)
                    driver.get(URL)
                    # Accept Cookies https://stackoverflow.com/questions/65056154/handling-accept-cookies-popup-with-selenium-in-python
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "// *[ @ id = 'sp-cc-accept']"))).click()
                    # https://stackoverflow.com/questions/20986631/how-can-i-scroll-a-web-page-using-selenium-webdriver-in-python
                    driver.execute_script("window.scrollTo(document.body.scrollHeight, 0);")

                    html = driver.page_source
                    soup = BeautifulSoup(html, features="lxml")
                    results = soup.find("div", id="tmmSwatches")
                    results2 = results.findAll("li")
                    counter = 0
                    found_selected_button = False
                    for list_item in results2:
                        if list_item.get("class")[1] == "selected":
                            found_selected_button = True
                            break
                        else:
                            counter += 1

                    if found_selected_button == True:
                        # print(counter)
                        if counter == 0:
                            WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH,
                                     "//*[@id='tmmSwatches']/ul/li[1]/span/span[3]/span[1]/span/a"))).click()

                        if counter == 1:
                            WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH,
                                     "//*[@id='tmmSwatches']/ul/li[2]/span/span[3]/span[1]/span/a"))).click()
                        elif counter == 2:
                            WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH,
                                     "//*[@id='tmmSwatches']/ul/li[3]/span/span[3]/span[1]/span/a"))).click()
                        elif counter == 3:
                            WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH,
                                     "//*[@id='tmmSwatches']/ul/li[4]/span/span[3]/span[1]/span/a"))).click()
                        elif counter == 4:
                            WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH,
                                     "//*[@id='tmmSwatches']/ul/li[5]/span/span[3]/span[1]/span/a"))).click()
                    else:
                        raise Exception

                    time.sleep(3)

                    html = driver.page_source
                    soup = BeautifulSoup(html, features="lxml")
                    results = soup.find("div", id="aod-offer")
                    price_text = results.find("span", class_="a-offscreen").get_text()

                    if results is not None:
                        price_without_sign = price_text[1:]
                        used_product_price = price_without_sign
                        print("Used Product Price: £" + str(price_without_sign))
                    else:
                        used_product_price = -999
                        print("Used Product Price: FAIL")
                except:
                    used_product_price = -999.00
                    print("Used Product Price: FAIL")

                # Used Delivery Price
                try:
                    results1 = soup.find("div",
                                         class_="a-section a-spacing-none a-padding-base aod-information-block aod-clear-float")
                    results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                    if (results2["data-csa-c-delivery-price"] == "FREE"):
                        print("Used Delivery Price: " + results2["data-csa-c-delivery-price"])
                        used_delivery_price = 0
                    else:
                        delivery_price_without_sign = results2["data-csa-c-delivery-price"][1:]
                        print("Used Delivery Price: " + delivery_price_without_sign)
                        used_delivery_price = delivery_price_without_sign

                except Exception as e:
                    print(e)
                    used_delivery_price = -999
                    print("Used Delivery Price: FAIL")


            except Exception as e:
                # New Product Price wasn't findable.
                # NEW PRODUCT NOT FOUND
                # ONLY USED PRODUCT EXISTS OR NO PRODUCT AVAILABLE AT ALL.

                try:
                    URL = "https://www.amazon.co.uk/dp/" + str(isbn)
                    driver.get(URL)
                    html = driver.page_source
                    soup = BeautifulSoup(html, features="lxml")
                    results = soup.find("div", id="tmmSwatches")
                    results2 = results.findAll("li")
                    counter = 0
                    found_selected_button = False
                    for list_item in results2:
                        if list_item.get("class")[1] == "selected":
                            found_selected_button = True
                            break
                        else:
                            counter += 1

                    span_block = results2[counter].findAll("span", attrs={'data-show-all-offers-display': True})

                    for loop_counter, block in enumerate(span_block):
                        stringer = (block['data-show-all-offers-display'])

                        if "used" in stringer:
                            pass
                        elif "new" in stringer:
                            index_of_new = loop_counter

                    if found_selected_button == True:
                        counter = counter
                        try:
                            index_of_new = index_of_new
                        except:
                            # NO NEW PRICE EXISTS!!
                            new_product_price = -999
                            new_delivery_price = -999

                            # find used prices secondary way

                            URL = "https://www.amazon.co.uk/dp/" + str(isbn)
                            driver.get(URL)
                            html = driver.page_source
                            soup = BeautifulSoup(html, features="lxml")

                            try:
                                click_used_link(driver, soup)

                                html = driver.page_source
                                soup = BeautifulSoup(html, features="lxml")
                                results = soup.find("span", class_="a-offscreen")
                                if results is not None:
                                    price = results.get_text()
                                    price_without_sign = price[1:]
                                    used_product_price = price_without_sign
                                    if "age" in used_product_price:
                                        html = driver.page_source
                                        soup = BeautifulSoup(html, features="lxml")
                                        results = soup.find("div", id="aod-offer")
                                        price_text = results.find("span", class_="a-offscreen").get_text()

                                        if results is not None:
                                            price_without_sign = price_text[1:]
                                            used_product_price = price_without_sign
                                            print("Used Product Price: £" + str(price_without_sign))
                                        else:
                                            used_product_price = -999
                                            print("Used Product Price: FAIL")
                                    else:
                                        print("Used Product Price: £" + str(price_without_sign))
                                else:
                                    used_product_price = -999
                                    print("Used Product Price: FAIL")

                                # Used Delivery Price
                                try:
                                    results1 = soup.find("div",
                                                         id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                                    results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                                    print("Used delivery price: £" + results2["data-csa-c-delivery-price"][1:])
                                    if (results2["data-csa-c-delivery-price"] == "FREE"):
                                        used_delivery_price = 0
                                    else:
                                        used_delivery_price = float(results2["data-csa-c-delivery-price"][1:])
                                except Exception as e:
                                    used_delivery_price = -999
                                    print("Used Delivery Price: FAIL")
                                    print(e)

                            except Exception as e:
                                used_product_price = -999
                                used_delivery_price = -999
                                print("Secondary method for used item failed. (1)")
                                print(e)
                                print("new_product_price: " + str(new_product_price))
                                print("new_delivery_price: " + str(new_delivery_price))

                            print()
                            end_of_item_loop(amazon_link, book_name, driver, edition_format, isbn, new_delivery_price, new_product_price, time1, used_delivery_price, used_product_price)
                            continue

                        if counter == 0:
                            xpath_string = "//*[@id='tmmSwatches']/ul/li/span/span[3]/span[" + str(
                                index_of_new + 1) + "]/span/a"
                        else:
                            xpath_string = "//*[@id='tmmSwatches']/ul/li[" + str(
                                counter + 1) + "]/span/span[3]/span[" + str(
                                index_of_new + 1) + "]/span/a"

                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, xpath_string))).click()

                    else:
                        raise Exception

                    time.sleep(3)

                    html = driver.page_source
                    soup = BeautifulSoup(html, features="lxml")
                    results = soup.find("div", id="aod-offer")
                    price_text = results.find("span", class_="a-offscreen").get_text()
                    new_product_price = price_text
                    print("New Product Price: " + str(new_product_price))

                    # New Delivery Price
                    try:
                        results1 = soup.find("div",
                                             class_="a-section a-spacing-none a-padding-base aod-information-block aod-clear-float")
                        results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                        if (results2["data-csa-c-delivery-price"] == "FREE"):
                            print("New Delivery Price: " + results2["data-csa-c-delivery-price"])
                            new_delivery_price = 0
                        else:
                            delivery_price_without_sign = results2["data-csa-c-delivery-price"][1:]
                            print("New Delivery Price: £" + delivery_price_without_sign)
                            new_delivery_price = delivery_price_without_sign

                    except Exception as e:
                        # New Delivery Price
                        try:
                            print("CHECK")
                            results1 = soup.find("div",
                                                 id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                            results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})

                            if (results2["data-csa-c-delivery-price"] == "FREE"):
                                new_delivery_price = 0
                                print("New Delivery Price: £0.00")
                            else:
                                new_delivery_price = float(results2["data-csa-c-delivery-price"][1:])
                                print("New Delivery Price: £" + results2["data-csa-c-delivery-price"])
                        except:
                            new_delivery_price = -999
                            print("New Delivery Price: FAIL")

                except Exception as e:
                    new_product_price = -999
                    new_delivery_price = -999
                    print("Except: New price doesn't exist")
                    # print(e)

                # Normal Secondary FOR USED PRICE
                URL = "https://www.amazon.co.uk/dp/" + str(isbn)
                driver.get(URL)
                html = driver.page_source
                soup = BeautifulSoup(html, features="lxml")

                try:
                    click_used_link(driver, soup)

                    html = driver.page_source
                    soup = BeautifulSoup(html, features="lxml")
                    results = soup.find("span", class_="a-offscreen")
                    if results is not None:
                        price = results.get_text()
                        price_without_sign = price[1:]
                        used_product_price = price_without_sign
                        if "age" in used_product_price:
                            html = driver.page_source
                            soup = BeautifulSoup(html, features="lxml")
                            results = soup.find("div", id="aod-offer")
                            price_text = results.find("span", class_="a-offscreen").get_text()

                            if results is not None:
                                price_without_sign = price_text[1:]
                                used_product_price = price_without_sign
                                print("Used Product Price: £" + str(price_without_sign))
                            else:
                                used_product_price = -999
                                print("Used Product Price: FAIL")
                        else:
                            print("Used Product Price: £" + str(price_without_sign))
                    else:
                        used_product_price = -999
                        print("Used Product Price: FAIL")

                    # Used Delivery Price
                    try:
                        results1 = soup.find("div",
                                             id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                        results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                        if (results2["data-csa-c-delivery-price"] == "FREE") or (
                                results2["data-csa-c-delivery-price"] == "REE"):
                            used_delivery_price = 0
                            print("Used delivery price: £0.00")
                        else:
                            used_delivery_price = float(results2["data-csa-c-delivery-price"][1:])
                            print("Used delivery price: £" + results2["data-csa-c-delivery-price"][1:])
                    except Exception as e:
                        used_delivery_price = -999
                        print("Used Delivery Price: FAIL")
                        print(e)

                except:
                    used_product_price = -999
                    used_delivery_price = -999
                    print("Secondary method for used item failed. (2)")
                    print("new_product_price: " + str(new_product_price))
                    print("new_delivery_price: " + str(new_delivery_price))

        except Exception as e:
            print("Except: Whole try-catch block for new products")
            print(e)
            driver.quit()
            return False

        end_of_item_loop(amazon_link, book_name, driver, edition_format, isbn, new_delivery_price, new_product_price, time1, used_delivery_price, used_product_price)
    return True



def check_amazon_prices_today_isbn(isbn, amazon_link, book_name, edition_format):
    # https://www.andressevilla.com/running-chromedriver-with-python-selenium-on-heroku/
    service = Service(os.environ.get("CHROMEDRIVER_PATH"))
    options = webdriver.ChromeOptions()

    # Settings Needed for Heroku
    options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    # https://stackoverflow.com/questions/12211781/how-to-maximize-window-in-chrome-using-webdriver-python
    #options.add_argument("--start-maximized")
    # https://stackoverflow.com/questions/11613869/how-to-disable-logging-using-selenium-with-python-binding
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless=new")
    options.add_argument('--blink-settings=imagesEnabled=false')
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    isbn = isbn.zfill(10)


    time1 = datetime.now()

    try:
        driver = webdriver.Chrome(service=service, options=options)
    except:
        print("Error with Selenium.")
        try:
            driver.quit()
        except:
            return
        return

    # NEW PRODUCTS
    # NEW PRODUCT PRICES AND NEW DELIVERY PRICES
    try:
        URL = "https://www.amazon.co.uk/dp/" + str(isbn)
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
                new_product_price = price_without_sign
                if "age" in new_product_price:
                    html = driver.page_source
                    soup = BeautifulSoup(html, features="lxml")
                    results = soup.find("div", id="aod-offer")
                    price_text = results.find("span", class_="a-offscreen").get_text()

                    if results is not None:
                        price_without_sign = price_text[1:]
                        new_product_price = price_without_sign
                        print("New Product Price: £" + str(price_without_sign))
                    else:
                        new_product_price = -999
                        print("New Product Price: FAIL")
                elif "%" in new_product_price:
                    # Used product on buy-box. New price definitely exists. Used price may not exist.
                    try:
                        # Click on link for new items.
                        click_new_link(driver, soup)
                        html = driver.page_source
                        soup = BeautifulSoup(html, features="lxml")
                        # New Product Price
                        results = soup.find("div",
                                            class_="a-section a-spacing-none a-padding-base aod-information-block aod-clear-float")
                        price_text = results.find("span", class_="a-offscreen").get_text()
                        new_product_price = price_text[1:]
                        print("New Product Price: " + str(new_product_price))

                        # New Delivery Price
                        results2 = results.find("span", attrs={'data-csa-c-delivery-price': True})
                        if (results2["data-csa-c-delivery-price"] == "FREE"):
                            print("New Delivery Price: " + results2["data-csa-c-delivery-price"])
                            new_delivery_price = 0
                        else:
                            delivery_price_without_sign = results2["data-csa-c-delivery-price"][1:]
                            print("New Delivery Price: £" + delivery_price_without_sign)
                            new_delivery_price = delivery_price_without_sign

                        # Go back to main product listing page.
                        driver.get(URL)
                        html = driver.page_source
                        soup = BeautifulSoup(html, features="lxml")

                        # Get Used prices
                        try:
                            # Click Used link
                            click_used_link(driver, soup)

                            html = driver.page_source
                            soup = BeautifulSoup(html, features="lxml")
                            results = soup.find("div",
                                                class_="a-section a-spacing-none asin-container-padding aod-clear-float")
                            # Used Product Price
                            price_text = results.find("span", class_="a-offscreen").get_text()
                            used_product_price = price_text[1:]

                            results1 = results.find("div",
                                                    id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                            results2 = results1.find("span",
                                                     attrs={'data-csa-c-delivery-price': True})
                            print("New delivery price: " + results2["data-csa-c-delivery-price"])
                            if (results2["data-csa-c-delivery-price"] == "FREE"):
                                new_delivery_price = 0
                            else:
                                try:
                                    if "£" in results2["data-csa-c-delivery-price"]:
                                        new_delivery_price = \
                                            re.findall("\d+\.\d+",
                                                       results2["data-csa-c-delivery-price"])[0]
                                        new_delivery_price = float(new_delivery_price)
                                    else:
                                        new_delivery_price = float(
                                            results2["data-csa-c-delivery-price"])
                                except:
                                    # new_product_price isn't a string
                                    new_delivery_price = float(
                                        results2["data-csa-c-delivery-price"])
                        except:
                            used_product_price = -999
                            used_delivery_price = -999
                    except Exception as e:
                        print("% Handler failed.")
                        new_product_price = -999
                        new_delivery_price = -999
                        used_product_price = -999
                        used_delivery_price = -999
                        print(e)

                    end_of_item_loop(amazon_link, book_name, driver, edition_format, isbn, new_delivery_price,
                                     new_product_price, time1, used_delivery_price, used_product_price)
                    return
                else:
                    print("New Product Price: £" + str(price_without_sign))
            else:
                new_product_price = -999
                print("New Product Price: FAIL")

            # New Delivery Price
            try:
                results1 = soup.find("div", id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                print("New delivery price: " + results2["data-csa-c-delivery-price"])
                if (results2["data-csa-c-delivery-price"] == "FREE"):
                    new_delivery_price = 0
                else:
                    try:
                        if "£" in results2["data-csa-c-delivery-price"]:
                            new_delivery_price = re.findall("\d+\.\d+", results2["data-csa-c-delivery-price"])[
                                0]
                            new_delivery_price = float(new_delivery_price)
                        else:
                            new_delivery_price = float(results2["data-csa-c-delivery-price"])
                    except:
                        # new_product_price isn't a string
                        new_delivery_price = float(results2["data-csa-c-delivery-price"])

            except Exception as e:
                # Secondary method of finding new delivery price
                # https://www.amazon.co.uk/dp/0786968982
                try:
                    results1 = soup.find("div", id="mir-layout-DELIVERY_BLOCK-slot-NO_PROMISE_UPSELL_MESSAGE")
                    results2 = results1.get_text()
                    if ("FREE" in results2) or ("free" in results2) or ("Free" in results2):
                        new_delivery_price = 0
                        print("New Delivery Price: £0.00")
                    else:
                        new_delivery_price = re.findall("\d+\.\d+", results2)[0]
                        print("New Delivery Price: £" + str(new_delivery_price))
                except Exception as e:
                    # Tertiary method of finding new delivery price
                    # https://www.amazon.co.uk/dp/0786967439
                    try:
                        results1 = soup.find("div", id="delivery-block-ags-dcp-container_0")
                        results2 = results1.get_text()
                        print(results2)
                        if ("FREE delivery" in results2):
                            new_delivery_price = 0
                            print("New Delivery Price: £0.00")
                        else:
                            new_delivery_price = re.findall("\d+\.\d+", results2)[0]
                            print("New Delivery Price: £" + str(new_delivery_price))
                    except Exception as e:
                        new_delivery_price = -999
                        print("New Delivery Price: FAIL")

            # USED PRODUCTS
            # Normal method of finding used product and delivery prices
            try:
                URL = "https://www.amazon.co.uk/dp/" + str(isbn)
                driver.get(URL)
                # Accept Cookies https://stackoverflow.com/questions/65056154/handling-accept-cookies-popup-with-selenium-in-python
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "// *[ @ id = 'sp-cc-accept']"))).click()
                # https://stackoverflow.com/questions/20986631/how-can-i-scroll-a-web-page-using-selenium-webdriver-in-python
                driver.execute_script("window.scrollTo(document.body.scrollHeight, 0);")

                html = driver.page_source
                soup = BeautifulSoup(html, features="lxml")
                print("HERE1")
                results = soup.find("div", id="tmmSwatches")
                print(results.prettify())
                # https://www.amazon.co.uk/Batman-Arkham-Talia-al-Ghul/dp/1779509154/ref=tmm_pap_swatch_0?_encoding=UTF8&qid=&sr=Add
                print("HERE2")
                results2 = results.findAll("li")
                print("HERE3")
                counter = 0
                found_selected_button = False
                for list_item in results2:
                    print(list_item)
                    print()
                    print()
                    print()
                    if list_item.get("class")[1] == "selected":
                        found_selected_button = True
                        break
                    else:
                        counter += 1

                if found_selected_button == True:
                    # print(counter)
                    if counter == 0:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH,
                                 "//*[@id='tmmSwatches']/ul/li[1]/span/span[3]/span[1]/span/a"))).click()

                    if counter == 1:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH,
                                 "//*[@id='tmmSwatches']/ul/li[2]/span/span[3]/span[1]/span/a"))).click()
                    elif counter == 2:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH,
                                 "//*[@id='tmmSwatches']/ul/li[3]/span/span[3]/span[1]/span/a"))).click()
                    elif counter == 3:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH,
                                 "//*[@id='tmmSwatches']/ul/li[4]/span/span[3]/span[1]/span/a"))).click()
                    elif counter == 4:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH,
                                 "//*[@id='tmmSwatches']/ul/li[5]/span/span[3]/span[1]/span/a"))).click()
                else:
                    raise Exception

                time.sleep(3)

                html = driver.page_source
                soup = BeautifulSoup(html, features="lxml")
                print("HERE4")
                results = soup.find("div", id="aod-offer")
                print("HERE5")
                price_text = results.find("span", class_="a-offscreen").get_text()

                if results is not None:
                    price_without_sign = price_text[1:]
                    used_product_price = price_without_sign
                    print("Used Product Price: £" + str(price_without_sign))
                else:
                    used_product_price = -999
                    print("Used Product Price: FAIL")
            except:
                used_product_price = -999.00
                print("Used Product Price: FAIL")

            # Used Delivery Price
            try:
                results1 = soup.find("div",
                                     class_="a-section a-spacing-none a-padding-base aod-information-block aod-clear-float")
                results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                if (results2["data-csa-c-delivery-price"] == "FREE"):
                    print("Used Delivery Price: " + results2["data-csa-c-delivery-price"])
                    used_delivery_price = 0
                else:
                    delivery_price_without_sign = results2["data-csa-c-delivery-price"][1:]
                    print("Used Delivery Price: " + delivery_price_without_sign)
                    used_delivery_price = delivery_price_without_sign

            except Exception as e:
                print(e)
                used_delivery_price = -999
                print("Used Delivery Price: FAIL")


        except Exception as e:
            # New Product Price wasn't findable.
            # NEW PRODUCT NOT FOUND
            # ONLY USED PRODUCT EXISTS OR NO PRODUCT AVAILABLE AT ALL.

            try:
                URL = "https://www.amazon.co.uk/dp/" + str(isbn)
                driver.get(URL)
                html = driver.page_source
                soup = BeautifulSoup(html, features="lxml")
                results = soup.find("div", id="tmmSwatches")
                results2 = results.findAll("li")
                counter = 0
                found_selected_button = False
                for list_item in results2:
                    if list_item.get("class")[1] == "selected":
                        found_selected_button = True
                        break
                    else:
                        counter += 1

                span_block = results2[counter].findAll("span", attrs={'data-show-all-offers-display': True})

                for loop_counter, block in enumerate(span_block):
                    stringer = (block['data-show-all-offers-display'])

                    if "used" in stringer:
                        pass
                    elif "new" in stringer:
                        index_of_new = loop_counter

                if found_selected_button == True:
                    counter = counter
                    try:
                        index_of_new = index_of_new
                    except:
                        # NO NEW PRICE EXISTS!!
                        new_product_price = -999
                        new_delivery_price = -999

                        # find used prices secondary way

                        URL = "https://www.amazon.co.uk/dp/" + str(isbn)
                        driver.get(URL)
                        html = driver.page_source
                        soup = BeautifulSoup(html, features="lxml")

                        try:
                            click_used_link(driver, soup)

                            html = driver.page_source
                            soup = BeautifulSoup(html, features="lxml")
                            results = soup.find("span", class_="a-offscreen")
                            if results is not None:
                                price = results.get_text()
                                price_without_sign = price[1:]
                                used_product_price = price_without_sign
                                if "age" in used_product_price:
                                    html = driver.page_source
                                    soup = BeautifulSoup(html, features="lxml")
                                    results = soup.find("div", id="aod-offer")
                                    price_text = results.find("span", class_="a-offscreen").get_text()

                                    if results is not None:
                                        price_without_sign = price_text[1:]
                                        used_product_price = price_without_sign
                                        print("Used Product Price: £" + str(price_without_sign))
                                    else:
                                        used_product_price = -999
                                        print("Used Product Price: FAIL")
                                else:
                                    print("Used Product Price: £" + str(price_without_sign))
                            else:
                                used_product_price = -999
                                print("Used Product Price: FAIL")

                            # Used Delivery Price
                            try:
                                results1 = soup.find("div",
                                                     id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                                results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                                print("Used delivery price: £" + results2["data-csa-c-delivery-price"][1:])
                                if (results2["data-csa-c-delivery-price"] == "FREE"):
                                    used_delivery_price = 0
                                else:
                                    used_delivery_price = float(results2["data-csa-c-delivery-price"][1:])
                            except Exception as e:
                                used_delivery_price = -999
                                print("Used Delivery Price: FAIL")
                                print(e)

                        except Exception as e:
                            used_product_price = -999
                            used_delivery_price = -999
                            print("Secondary method for used item failed. (1)")
                            print(e)
                            print("new_product_price: " + str(new_product_price))
                            print("new_delivery_price: " + str(new_delivery_price))

                        print()
                        end_of_item_loop(amazon_link, book_name, driver, edition_format, isbn, new_delivery_price, new_product_price, time1, used_delivery_price, used_product_price)
                        return

                    if counter == 0:
                        xpath_string = "//*[@id='tmmSwatches']/ul/li/span/span[3]/span[" + str(
                            index_of_new + 1) + "]/span/a"
                    else:
                        xpath_string = "//*[@id='tmmSwatches']/ul/li[" + str(
                            counter + 1) + "]/span/span[3]/span[" + str(
                            index_of_new + 1) + "]/span/a"

                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, xpath_string))).click()

                else:
                    raise Exception

                time.sleep(3)

                html = driver.page_source
                soup = BeautifulSoup(html, features="lxml")
                results = soup.find("div", id="aod-offer")
                price_text = results.find("span", class_="a-offscreen").get_text()
                new_product_price = price_text
                print("New Product Price: " + str(new_product_price))

                # New Delivery Price
                try:
                    results1 = soup.find("div",
                                         class_="a-section a-spacing-none a-padding-base aod-information-block aod-clear-float")
                    results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                    if (results2["data-csa-c-delivery-price"] == "FREE"):
                        print("New Delivery Price: " + results2["data-csa-c-delivery-price"])
                        new_delivery_price = 0
                    else:
                        delivery_price_without_sign = results2["data-csa-c-delivery-price"][1:]
                        print("New Delivery Price: £" + delivery_price_without_sign)
                        new_delivery_price = delivery_price_without_sign

                except Exception as e:
                    # New Delivery Price
                    try:
                        print("CHECK")
                        results1 = soup.find("div",
                                             id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                        results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})

                        if (results2["data-csa-c-delivery-price"] == "FREE"):
                            new_delivery_price = 0
                            print("New Delivery Price: £0.00")
                        else:
                            new_delivery_price = float(results2["data-csa-c-delivery-price"][1:])
                            print("New Delivery Price: £" + results2["data-csa-c-delivery-price"])
                    except:
                        new_delivery_price = -999
                        print("New Delivery Price: FAIL")

            except Exception as e:
                new_product_price = -999
                new_delivery_price = -999
                print("Except: New price doesn't exist")
                # print(e)

            # Normal Secondary FOR USED PRICE
            URL = "https://www.amazon.co.uk/dp/" + str(isbn)
            driver.get(URL)
            html = driver.page_source
            soup = BeautifulSoup(html, features="lxml")

            try:
                click_used_link(driver, soup)

                html = driver.page_source
                soup = BeautifulSoup(html, features="lxml")
                results = soup.find("span", class_="a-offscreen")
                if results is not None:
                    price = results.get_text()
                    price_without_sign = price[1:]
                    used_product_price = price_without_sign
                    if "age" in used_product_price:
                        html = driver.page_source
                        soup = BeautifulSoup(html, features="lxml")
                        results = soup.find("div", id="aod-offer")
                        price_text = results.find("span", class_="a-offscreen").get_text()

                        if results is not None:
                            price_without_sign = price_text[1:]
                            used_product_price = price_without_sign
                            print("Used Product Price: £" + str(price_without_sign))
                        else:
                            used_product_price = -999
                            print("Used Product Price: FAIL")
                    else:
                        print("Used Product Price: £" + str(price_without_sign))
                else:
                    used_product_price = -999
                    print("Used Product Price: FAIL")

                # Used Delivery Price
                try:
                    results1 = soup.find("div",
                                         id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                    results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                    if (results2["data-csa-c-delivery-price"] == "FREE") or (
                            results2["data-csa-c-delivery-price"] == "REE"):
                        used_delivery_price = 0
                        print("Used delivery price: £0.00")
                    else:
                        used_delivery_price = float(results2["data-csa-c-delivery-price"][1:])
                        print("Used delivery price: £" + results2["data-csa-c-delivery-price"][1:])
                except Exception as e:
                    used_delivery_price = -999
                    print("Used Delivery Price: FAIL")
                    print(e)

            except:
                used_product_price = -999
                used_delivery_price = -999
                print("Secondary method for used item failed. (2)")
                print("new_product_price: " + str(new_product_price))
                print("new_delivery_price: " + str(new_delivery_price))

    except Exception as e:
        print("Except: Whole try-catch block for new products")
        print(e)
        driver.quit()
        return False

    end_of_item_loop(amazon_link, book_name, driver, edition_format, isbn, new_delivery_price, new_product_price, time1, used_delivery_price, used_product_price)
    return True







def click_used_link(driver, soup):
    results = soup.find("div", id="tmmSwatches")
    results2 = results.findAll("li")
    counter = 0
    found_selected_button = False
    for list_item in results2:
        if list_item.get("class")[1] == "selected":
            found_selected_button = True
            break
        else:
            counter += 1
    span_block = results2[counter].findAll("span",
                                           attrs={'data-show-all-offers-display': True})
    for loop_counter, block in enumerate(span_block):
        stringer = (block['data-show-all-offers-display'])

        if "used" in stringer:
            index_of_used = loop_counter
        elif "new" in stringer:
            pass
    if found_selected_button == True:
        counter = counter
        index_of_used = index_of_used
        if counter == 0:
            xpath_string = "//*[@id='tmmSwatches']/ul/li/span/span[3]/span[" + str(
                index_of_used + 1) + "]/span/a"
        else:
            xpath_string = "//*[@id='tmmSwatches']/ul/li[" + str(
                counter + 1) + "]/span/span[3]/span[" + str(
                index_of_used + 1) + "]/span/a"

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, xpath_string))).click()

    else:
        raise Exception
    time.sleep(3)
    return


def click_new_link(driver, soup):
    results = soup.find("div", id="tmmSwatches")
    results2 = results.findAll("li")
    counter = 0
    found_selected_button = False
    for list_item in results2:
        if list_item.get("class")[1] == "selected":
            found_selected_button = True
            break
        else:
            counter += 1
    span_block = results2[counter].findAll("span", attrs={
        'data-show-all-offers-display': True})
    for loop_counter, block in enumerate(span_block):
        stringer = (block['data-show-all-offers-display'])

        if "used" in stringer:
            pass
        elif "new" in stringer or "all" in stringer:
            index_of_new = loop_counter
    if found_selected_button == True:
        counter = counter
    index_of_new = index_of_new
    if counter == 0:
        xpath_string = "//*[@id='tmmSwatches']/ul/li/span/span[3]/span[" + str(
            index_of_new + 1) + "]/span/a"
    else:
        xpath_string = "//*[@id='tmmSwatches']/ul/li[" + str(
            counter + 1) + "]/span/span[3]/span[" + str(
            index_of_new + 1) + "]/span/a"
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, xpath_string))).click()
    time.sleep(3)
    return


def end_of_item_loop(amazon_link, book_name, driver, edition_format, isbn, new_delivery_price, new_product_price,
                     time1, used_delivery_price, used_product_price):
    time2 = datetime.now()
    time_diff = time2 - time1
    print("Time: ", time_diff.seconds)
    print()

    try:
        if "£" in new_product_price:
            new_product_price = re.findall("\d+\.\d+", new_product_price)[0]
    except:
        # new_product_price isn't a string
        pass

    try:
        new_total_price_raw = float(new_product_price) + float(new_delivery_price)
    except:
        new_product_price = -999
        new_delivery_price = -999
        new_total_price_raw = -999
    if new_total_price_raw <= -1000 or new_total_price_raw >= 1000:
        new_total_price_raw = -999
    try:
        used_total_price_raw = float(used_product_price) + float(
            used_delivery_price)
    except:
        used_product_price = -999
        used_delivery_price = -999
        used_total_price_raw = -999
    if used_total_price_raw <= -1000 or used_total_price_raw >= 1000:
        used_total_price_raw = -999
    try:
        new_book = app.Amazon(book_name=book_name, amazon_link=amazon_link,
                              isbn=isbn, edition_format=edition_format,
                              new_product_price=[new_product_price],
                              new_delivery_price=[new_delivery_price],
                              new_total_price=[new_total_price_raw],
                              used_product_price=[used_product_price],
                              used_delivery_price=[used_delivery_price],
                              used_total_price=[used_total_price_raw])
        app.db.session.add(new_book)
        app.db.session.commit()

    except IntegrityError:
        app.db.session.rollback()
        book_to_append_amazon = app.Amazon.query.get_or_404(isbn)

        # If previous price was found, but not found now, then it means that the book must have sold recently.
        # Price is set at the last known price.
        try:
            if float(new_total_price_raw) == -999 and book_to_append_amazon.new_total_price[-1] != -999:
                new_product_price = book_to_append_amazon.new_product_price[-1]
                new_delivery_price = book_to_append_amazon.new_delivery_price[-1]
                new_total_price_raw = book_to_append_amazon.new_total_price[-1]
                print("NEW: IDENTIFIED SOLD BOOK PREVIOUSLY. COPYING PREVIOUS PRICE.")

            if float(used_total_price_raw) == -999 and book_to_append_amazon.used_total_price[-1] != -999:
                used_product_price = book_to_append_amazon.used_product_price[-1]
                used_delivery_price = book_to_append_amazon.used_delivery_price[-1]
                used_total_price_raw = book_to_append_amazon.used_total_price[-1]
                print("USED: IDENTIFIED SOLD BOOK PREVIOUSLY. COPYING PREVIOUS PRICE.")
        except Exception as e:
            print("ERROR: Failed to set price at last known price, despite price not found now.")
            print(e)

        book_to_append_amazon.new_product_price = book_to_append_amazon.new_product_price + [new_product_price]
        book_to_append_amazon.new_delivery_price = book_to_append_amazon.new_delivery_price + [new_delivery_price]
        book_to_append_amazon.new_total_price = book_to_append_amazon.new_total_price + [new_total_price_raw]
        book_to_append_amazon.used_product_price = book_to_append_amazon.used_product_price + [used_product_price]
        book_to_append_amazon.used_delivery_price = book_to_append_amazon.used_delivery_price + [used_delivery_price]
        book_to_append_amazon.used_total_price = book_to_append_amazon.used_total_price + [used_total_price_raw]
        try:
            app.db.session.commit()
        except:
            app.db.session.rollback()
    except:
        app.db.session.rollback()
    driver.quit()


def setup_database(links,base_file_name="scraped_database_data", create_new_csv=False, add_bestseller_link=False, scrape_prices=True, scrape_only_new_books=False):

    if create_new_csv:
        create_blank_csv("./"+ base_file_name +"_amazon.csv", createHeader=True)

        for link in links:
            setup_list_one_page_from_amazon("./"+ base_file_name +"_amazon.csv",link)

        get_ISBN_from_list("./"+ base_file_name +"_amazon.csv")

    if add_bestseller_link:
        for link in links:
            setup_list_one_page_from_amazon("./"+ base_file_name +"_amazon.csv",link)

        get_ISBN_from_list("./"+ base_file_name +"_amazon.csv")

    create_blank_csv("./" + base_file_name + "_ebay.csv")

    # Copy to ebay Excel file
    df = pd.read_csv("./" + base_file_name + "_amazon.csv")
    isbn_column = df.iloc[:, [3]]
    number_of_rows = df.shape[0]
    new_links_list = []
    used_links_list = []
    for row_number in range(number_of_rows):
        isbn_in_row = df.iloc[row_number, [3]]
        isbn_element = isbn_in_row[0]
        isbn_element = isbn_element.zfill(10)
        new_link = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
            isbn_element) + "&_sacat=0&_sop=15&LH_ItemCondition=3&LH_PrefLoc=2&rt=nc&LH_BIN=1"
        used_link = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
            isbn_element) + "&_sacat=0&_sop=15&LH_BIN=1&LH_PrefLoc=1&rt=nc&LH_ItemCondition=4"
        new_links_list.append(new_link)
        used_links_list.append(used_link)
    df["New Link"] = new_links_list
    df["Used Link"] = used_links_list
    df = df.drop('Link', axis=1)
    # https://stackoverflow.com/questions/13148429/how-to-change-the-order-of-dataframe-columns
    df = df[['Title', 'New Link', 'Used Link', 'Edition Format', 'ISBN']]
    df.to_csv("./" + base_file_name + "_ebay.csv", index=False)

    if scrape_prices and scrape_only_new_books:
        check_amazon_prices_today("./" + base_file_name + "_amazon.csv", only_create_new_books=True)
        check_ebay_prices_today("./" + base_file_name + "_ebay.csv", only_create_new_books=True)

    if scrape_prices and not scrape_only_new_books:
        check_amazon_prices_today("./" + base_file_name + "_amazon.csv", only_create_new_books=False)
        check_ebay_prices_today("./" + base_file_name + "_ebay.csv", only_create_new_books=False)


def get_ebay_historical_price(isbn, condition):

    if condition.lower()=="new":
        # URL = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
        #     isbn) + "&_sacat=0&LH_Sold=1&LH_Complete=1&LH_PrefLoc=1&rt=nc"

        # https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=%091622127226&_sacat=0&LH_ItemCondition=3&LH_PrefLoc=2&rt=nc&LH_Sold=1&LH_Complete=1
        URL = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=%09" + str(isbn) + "&_sacat=0&LH_ItemCondition=3&LH_PrefLoc=2&rt=nc&LH_Sold=1&LH_Complete=1"

        page = requests.get(URL)
        html = page.text
        soup = BeautifulSoup(html, features="lxml")

        try:
            sum=0
            count=0
            results = soup.find("ul", class_="srp-results srp-list clearfix")
            historical_new_product_price_list = results.findAll("span", class_="s-item__price")
            try:
                historical_new_product_price_with_sign = historical_new_product_price_list[0].get_text()
                historical_new_product_price = historical_new_product_price_with_sign[1:]
                sum += float(historical_new_product_price)

                index = 0
                new_delivery_price = get_new_delivery_price(index, soup)
                sum += float(new_delivery_price)

                try:
                    historical_new_product_price_with_sign = historical_new_product_price_list[1].get_text()
                    historical_new_product_price = historical_new_product_price_with_sign[1:]
                    sum += float(historical_new_product_price)

                    index = 1
                    new_delivery_price = get_new_delivery_price(index, soup)
                    sum += float(new_delivery_price)
                    try:
                        historical_new_product_price_with_sign = historical_new_product_price_list[2].get_text()
                        historical_new_product_price = historical_new_product_price_with_sign[1:]
                        sum += float(historical_new_product_price)

                        index = 2
                        new_delivery_price = get_new_delivery_price(index, soup)
                        sum += float(new_delivery_price)

                        historical_new_product_price = sum/3
                        return historical_new_product_price
                    except Exception as e:
                        historical_new_product_price = sum/2
                        return historical_new_product_price
                except Exception as e:
                    historical_new_product_price = sum/1
                    return historical_new_product_price
            except Exception as e:
                historical_new_product_price = -999
                return historical_new_product_price

        except Exception as e:
            historical_new_product_price = -999
            return historical_new_product_price


    elif condition.lower()=="used":
        # URL = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
        #     isbn) + "&_sacat=0&LH_ItemCondition=4&LH_Sold=1&LH_Complete=1&rt=nc&LH_PrefLoc=1"

        # https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=1622127226&_sacat=0&LH_ItemCondition=4&LH_PrefLoc=2&rt=nc&LH_Sold=1&LH_Complete=1
        URL = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
                    isbn) + "&_sacat=0&LH_ItemCondition=4&LH_PrefLoc=2&rt=nc&LH_Sold=1&LH_Complete=1"


        page = requests.get(URL)
        html = page.text
        soup = BeautifulSoup(html, features="lxml")

        try:
            sum=0
            count=0
            results = soup.find("ul", class_="srp-results srp-list clearfix")
            historical_used_product_price_list = results.findAll("span", class_="s-item__price")
            try:
                historical_used_product_price_with_sign = historical_used_product_price_list[0].get_text()
                historical_used_product_price = historical_used_product_price_with_sign[1:]
                sum += float(historical_used_product_price)

                index = 0
                used_delivery_price = get_used_delivery_price(index, soup)
                sum += float(used_delivery_price)

                try:
                    historical_used_product_price_with_sign = historical_used_product_price_list[1].get_text()
                    historical_used_product_price = historical_used_product_price_with_sign[1:]
                    sum += float(historical_used_product_price)

                    index = 1
                    used_delivery_price = get_used_delivery_price(index, soup)
                    sum += float(used_delivery_price)
                    try:
                        historical_used_product_price_with_sign = historical_used_product_price_list[2].get_text()
                        historical_used_product_price = historical_used_product_price_with_sign[1:]
                        sum += float(historical_used_product_price)

                        index = 2
                        used_delivery_price = get_used_delivery_price(index, soup)
                        sum += float(used_delivery_price)

                        historical_used_product_price = sum/3
                        return historical_used_product_price
                    except Exception as e:
                        historical_used_product_price = sum/2
                        return historical_used_product_price
                except Exception as e:
                    historical_used_product_price = sum/1
                    return historical_used_product_price
            except Exception as e:
                historical_used_product_price = -999
                return historical_used_product_price

        except Exception as e:
            historical_used_product_price = -999
            return historical_used_product_price

    else:
        pass

def get_new_delivery_price(index, soup):
    try:
        results = soup.find("ul", class_="srp-results")
        new_delivery_price_list = results.findAll("span", class_="s-item__shipping s-item__logisticsCost")
        new_delivery_price_with_sign = new_delivery_price_list[index].get_text()
        if (("Free" in new_delivery_price_with_sign) or ("free" in new_delivery_price_with_sign)) and (
                ("Postage" in new_delivery_price_with_sign) or (
                "postage" in new_delivery_price_with_sign)):
            new_delivery_price = 0
        else:
            new_delivery_price = re.findall("\d+\.\d+", new_delivery_price_with_sign)[0]
    except:
        try:
            results = soup.find("ul", class_="srp-results")
            new_delivery_price_list = results.findAll("span", class_="s-item__dynamic s-item__freeXDays")
            new_delivery_price_with_sign = new_delivery_price_list[index].get_text()
            if (("Free" in new_delivery_price_with_sign) or (
                    "free" in new_delivery_price_with_sign)) and (
                    ("Postage" in new_delivery_price_with_sign) or (
                    "postage" in new_delivery_price_with_sign)):
                new_delivery_price = 0
            else:
                # https://www.tutorialspoint.com/Extract-decimal-numbers-from-a-string-in-Python#:~:text=To%20extract%20decimal%20numbers%20from,to%20work%20with%20regular%20expressions.
                new_delivery_price = re.findall("\d+\.\d+", new_delivery_price_with_sign)[0]
        except Exception as e:
            new_delivery_price = -999
    return new_delivery_price

def get_used_delivery_price(index, soup):
    try:
        results = soup.find("ul", class_="srp-results")
        used_delivery_price_list = results.findAll("span", class_="s-item__shipping s-item__logisticsCost")
        used_delivery_price_with_sign = used_delivery_price_list[index].get_text()
        if (("Free" in used_delivery_price_with_sign) or ("free" in used_delivery_price_with_sign)) and (
                ("Postage" in used_delivery_price_with_sign) or (
                "postage" in used_delivery_price_with_sign)):
            used_delivery_price = 0
        else:
            used_delivery_price = re.findall("\d+\.\d+", used_delivery_price_with_sign)[0]
    except:
        try:
            results = soup.find("ul", class_="srp-results")
            used_delivery_price_list = results.findAll("span", class_="s-item__dynamic s-item__freeXDays")
            used_delivery_price_with_sign = used_delivery_price_list[index].get_text()
            if (("Free" in used_delivery_price_with_sign) or (
                    "free" in used_delivery_price_with_sign)) and (
                    ("Postage" in used_delivery_price_with_sign) or (
                    "postage" in used_delivery_price_with_sign)):
                used_delivery_price = 0
            else:
                # https://www.tutorialspoint.com/Extract-decimal-numbers-from-a-string-in-Python#:~:text=To%20extract%20decimal%20numbers%20from,to%20work%20with%20regular%20expressions.
                used_delivery_price = re.findall("\d+\.\d+", used_delivery_price_with_sign)[0]
        except Exception as e:
            used_delivery_price = -999
    return used_delivery_price


def update_names_in_database():
    books_amazon = app.Amazon.query.order_by(app.Amazon.book_name)

    for book in books_amazon:
        link = book.amazon_link
        old_book_name = book.book_name

        service = Service("..\chromedriver_win32")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1200")
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(link)

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

        # title
        span_element = soup.findAll("span", id="productTitle")

        if len(span_element) != 0:
            title = span_element[0].get_text()
            print(title)
        else:
            print("ERROR!")
            print(link)
            title = ""

        print()

        book.book_name = title
        try:
            app.db.session.commit()
            print("Book name updated from: \"" + old_book_name + "\" to \"" + title + "\".")
        except:
            app.db.session.rollback()
            return "There was an error updating that book in the database"

def update_ebay_historical_prices_in_database():
    books_ebay = app.Ebay.query.order_by(app.Ebay.book_name)

    for book in books_ebay:
        print(book.book_name)
        isbn = book.isbn
        used_historical_price = get_ebay_historical_price(isbn, "new")
        print(used_historical_price)
        book.historical_new_total_price = book.historical_new_total_price + [used_historical_price]

        new_historical_price = get_ebay_historical_price(isbn, "used")
        print(new_historical_price)
        book.historical_used_total_price = book.historical_used_total_price + [new_historical_price]

        try:
            app.db.session.commit()
            print("Committed.")
            print()
        except Exception as e:
            app.db.session.rollback()
            print ("There was an error updating that book in the database")
            print(e)




def main():
    links = [
        "https://www.amazon.co.uk/Best-Sellers-Books-Role-Playing-War-Games/zgbs/books/270509/ref=zg_bs_nav_books_3_270453",
        "https://www.amazon.co.uk/best-sellers-books-Amazon/zgbs/books/270509/ref=zg_bs_pg_2_books?_encoding=UTF8&pg=2",
        "https://www.amazon.co.uk/gp/bestsellers/books/503400/ref=pd_zg_hrsr_books",
        "https://www.amazon.co.uk/best-sellers-books-Amazon/zgbs/books/503400/ref=zg_bs_pg_2_books?_encoding=UTF8&pg=2",
        "https://www.amazon.co.uk/gp/bestsellers/books/14909604031/ref=pd_zg_hrsr_books",
        "https://www.amazon.co.uk/best-sellers-books-Amazon/zgbs/books/14909604031/ref=zg_bs_pg_2_books?_encoding=UTF8&pg=2"]

    # Only setup CSV files. Note, deletes old files!
    # setup_database(links, new_list=True, scrape_prices=False)

    #check_amazon_prices_today("./scraped_database_data_amazon.csv", only_create_new_books=False)
    check_ebay_prices_today("./scraped_database_data_ebay.csv", only_create_new_books=True)





if __name__ == "__main__":
    main()


