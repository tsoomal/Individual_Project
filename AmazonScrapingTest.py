import os
import re
from datetime import datetime
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC



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


def check_amazon_prices_today(file_name, only_create_new_books=False):
    new_product_prices_list = []
    new_delivery_prices_list = []
    used_product_prices_list = []
    used_delivery_prices_list = []

    df = pd.read_csv(file_name)
    number_of_rows = df.shape[0]

    service = Service(os.environ.get("CHROMEDRIVER_PATH"))
    options = webdriver.ChromeOptions()
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


        # New Products
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
                    new_product_prices_list.append(price_without_sign)
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
                            new_product_prices_list.append(-999)
                            print("New Product Price: FAIL")
                    else:
                        print("New Product Price: £" + str(price_without_sign))
                else:
                    new_product_price = -999
                    new_product_prices_list.append(-999)
                    print("New Product Price: FAIL")
            except Exception as e:
                new_product_price = -999
                print("Except: New Product price")
                print(e)

            # New Delivery Price
            try:
                results1 = soup.find("div", id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                print("New delivery price: " + results2["data-csa-c-delivery-price"])
                if (results2["data-csa-c-delivery-price"]=="FREE"):
                    new_delivery_price = 0
                    new_delivery_prices_list.append(0)
                else:
                    new_delivery_price = float(results2["data-csa-c-delivery-price"])
                    new_delivery_prices_list.append(results2["data-csa-c-delivery-price"])
            except:
                new_delivery_price = -999
                new_delivery_prices_list.append(-999)
                print("New Delivery Price: FAIL")

        except Exception as e:
            print("Except: Whole try-catch block for new products")
            print(e)
            driver.quit()
            return



        # Used Products
        try:
            # Used Product Price
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
                counter=0
                found_selected_button = False
                for list_item in results2:
                    if list_item.get("class")[1] == "selected":
                        found_selected_button = True
                        break
                    else:
                        counter+=1

                if found_selected_button==True:
                    #print(counter)
                    if counter ==0:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//*[@id='tmmSwatches']/ul/li[1]/span/span[3]/span[1]/span/a"))).click()
                        # //*[@id="tmmSwatches"]/ul/li/span/span[3]/span/span/a
                        # //*[@id="tmmSwatches"]/ul/li[4]/span/span[3]/span[1]/span/a

                    if counter ==1:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//*[@id='tmmSwatches']/ul/li[2]/span/span[3]/span[1]/span/a"))).click()
                    elif counter == 2:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//*[@id='tmmSwatches']/ul/li[3]/span/span[3]/span[1]/span/a"))).click()
                    elif counter == 3:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//*[@id='tmmSwatches']/ul/li[4]/span/span[3]/span[1]/span/a"))).click()
                    elif counter == 4:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//*[@id='tmmSwatches']/ul/li[5]/span/span[3]/span[1]/span/a"))).click()
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
                    used_product_prices_list.append(price_without_sign)
                    print("Used Product Price: £" + str(price_without_sign))
                else:
                    used_product_price = -999
                    used_product_prices_list.append(-999)
                    print("Used Product Price: FAIL")
            except:
                used_product_price = -999.00
                used_product_prices_list.append(-999)
                print("Used Product Price: FAIL")


            # Used Delivery Price
            try:
                results1 = soup.find("div", class_="a-section a-spacing-none a-padding-base aod-information-block aod-clear-float")
                results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                if (results2["data-csa-c-delivery-price"] == "FREE"):
                    print("Used Delivery Price: " + results2["data-csa-c-delivery-price"])
                    used_delivery_price = 0
                    used_delivery_prices_list.append(0)
                else:
                    delivery_price_without_sign = results2["data-csa-c-delivery-price"][1:]
                    print("Used Delivery Price: " + delivery_price_without_sign)
                    used_delivery_price = delivery_price_without_sign
                    used_delivery_prices_list.append(float(delivery_price_without_sign))

            except Exception as e:
                print(e)
                used_delivery_price = -999
                used_delivery_prices_list.append(-999)
                print("Used Delivery Price: FAIL")

        except:
            print("EXCEPTION: Try-catch block for Delivery Price")
            driver.quit()
            return


        time2 = datetime.now()
        time_diff = time2 - time1
        print("Time: ", time_diff.seconds)
        print()

        driver.quit()


def check_amazon_prices_today_isbn(file_name, isbn, only_create_new_books=False):

    service = Service(os.environ.get("CHROMEDRIVER_PATH"))
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless=new")
    options.add_argument('--blink-settings=imagesEnabled=false')
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    # https://stackoverflow.com/questions/27387415/how-would-i-get-everything-before-a-in-a-string-python
    isbn = isbn

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


    # New Products
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
                    new_delivery_price = float(results2["data-csa-c-delivery-price"])
            except:
                new_delivery_price = -999
                print("New Delivery Price: FAIL")

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
                                (By.XPATH, "//*[@id='tmmSwatches']/ul/li[1]/span/span[3]/span[1]/span/a"))).click()
                        # //*[@id="tmmSwatches"]/ul/li/span/span[3]/span/span/a
                        # //*[@id="tmmSwatches"]/ul/li[4]/span/span[3]/span[1]/span/a

                    if counter == 1:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//*[@id='tmmSwatches']/ul/li[2]/span/span[3]/span[1]/span/a"))).click()
                    elif counter == 2:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//*[@id='tmmSwatches']/ul/li[3]/span/span[3]/span[1]/span/a"))).click()
                    elif counter == 3:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//*[@id='tmmSwatches']/ul/li[4]/span/span[3]/span[1]/span/a"))).click()
                    elif counter == 4:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//*[@id='tmmSwatches']/ul/li[5]/span/span[3]/span[1]/span/a"))).click()
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

            try:
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

                #print(counter)

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

                        #find used prices secondary way

                        URL = "https://www.amazon.co.uk/dp/" + str(isbn)
                        driver.get(URL)
                        html = driver.page_source
                        soup = BeautifulSoup(html, features="lxml")

                        try:
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

                            # print(counter)

                            span_block = results2[counter].findAll("span", attrs={'data-show-all-offers-display': True})

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
                            print("Secondary method for used item failed.")
                            print(e)
                            print("new_product_price: " + str(new_product_price))
                            print("new_delivery_price: " + str(new_delivery_price))


                        return
                    if counter ==0:
                        xpath_string = "//*[@id='tmmSwatches']/ul/li/span/span[3]/span[" + str(index_of_new+1) + "]/span/a"
                    else:
                        xpath_string = "//*[@id='tmmSwatches']/ul/li[" + str(counter+1) + "]/span/span[3]/span[" + str(
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
                        results1 = soup.find("div", id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
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
                print("Except: New")
                print(e)

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
                        else:
                            print("New Product Price: £" + str(price_without_sign))
                    else:
                        new_product_price = -999
                        print("New Product Price: FAIL")
                except Exception as e:
                    used_delivery_price = -999
                    return

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
                    return

            # Normal Secondary FOR USED PRICE

            URL = "https://www.amazon.co.uk/dp/" + str(isbn)
            driver.get(URL)
            html = driver.page_source
            soup = BeautifulSoup(html, features="lxml")

            try:
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

                #print(counter)

                span_block = results2[counter].findAll("span", attrs={'data-show-all-offers-display': True})

                for loop_counter, block in enumerate(span_block):
                    stringer = (block['data-show-all-offers-display'])

                    if "used" in stringer:
                        index_of_used = loop_counter
                    elif "new" in stringer:
                        pass

                if found_selected_button == True:
                    counter = counter
                    index_of_used = index_of_used
                    if counter ==0:
                        xpath_string = "//*[@id='tmmSwatches']/ul/li/span/span[3]/span[" + str(index_of_used+1) + "]/span/a"
                    else:
                        xpath_string = "//*[@id='tmmSwatches']/ul/li[" + str(counter+1) + "]/span/span[3]/span[" + str(
                            index_of_used + 1) + "]/span/a"

                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, xpath_string))).click()

                else:
                    raise Exception

                time.sleep(3)

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
                    results1 = soup.find("div", id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                    results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                    if (results2["data-csa-c-delivery-price"] == "FREE") or (results2["data-csa-c-delivery-price"] == "REE"):
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
                print("Secondary method for used item failed.")
                print("new_product_price: " + str(new_product_price))
                print("new_delivery_price: " + str(new_delivery_price))

    except Exception as e:
        print("Except: Whole try-catch block for new products")
        print(e)
        driver.quit()
        return


    time2 = datetime.now()
    time_diff = time2 - time1
    print("Time: ", time_diff.seconds)
    print()

    driver.quit()




def check_amazon_prices_today_proper_test(file_name, only_create_new_books=False):
    df = pd.read_csv(file_name)
    number_of_rows = df.shape[0]

    # https://www.andressevilla.com/running-chromedriver-with-python-selenium-on-heroku/
    service = Service(os.environ.get("CHROMEDRIVER_PATH"))
    options = webdriver.ChromeOptions()

    # Settings Needed for Heroku
    #options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    #options.add_argument("--disable-dev-shm-usage")
    #options.add_argument("--no-sandbox")

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

        # if isbn == "1852865164" or isbn == "1852867329" or isbn == "1563893436":
        #     pass
        # else:
        #     continue

        # if isbn == "1858755832" or isbn == "1801262098" or isbn == "1840231246" or isbn == "185286480X":
        #     pass
        # else:
        #     continue

        # if isbn == "1858755832":
        #     pass
        # else:
        #     continue


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
                return False
            return False

        # INSERT HERE

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
                            driver.get_screenshot_as_file("./screenshot.png")
                            html = driver.page_source
                            soup = BeautifulSoup(html, features="lxml")
                            # New Product Price
                            results = soup.find("div", class_="a-section a-spacing-none a-padding-base aod-information-block aod-clear-float")
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

                                html = driver.page_source
                                soup = BeautifulSoup(html, features="lxml")
                                results = soup.find("div", class_="a-section a-spacing-none asin-container-padding aod-clear-float")
                                # Used Product Price
                                price_text = results.find("span", class_="a-offscreen").get_text()
                                used_product_price = price_text[1:]

                                results1 = results.find("div",
                                                     id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
                                results2 = results1.find("span", attrs={'data-csa-c-delivery-price': True})
                                print("New delivery price: " + results2["data-csa-c-delivery-price"])
                                if (results2["data-csa-c-delivery-price"] == "FREE"):
                                    new_delivery_price = 0
                                else:
                                    try:
                                        if "£" in results2["data-csa-c-delivery-price"]:
                                            new_delivery_price = \
                                            re.findall("\d+\.\d+", results2["data-csa-c-delivery-price"])[0]
                                            new_delivery_price = float(new_delivery_price)
                                        else:
                                            new_delivery_price = float(results2["data-csa-c-delivery-price"])
                                    except:
                                        # new_product_price isn't a string
                                        new_delivery_price = float(results2["data-csa-c-delivery-price"])
                            except:
                                used_product_price = -999
                                used_delivery_price = -999
                        except Exception as e:
                            print("% Handler failed.")
                            new_product_price=-999
                            new_delivery_price=-999
                            used_product_price=-999
                            used_delivery_price=-999
                            print(e)

                        print()
                        try:
                            if "£" in new_product_price:
                                new_product_price = re.findall("\d+\.\d+", new_product_price)[0]
                        except:
                            # new_product_price isn't a string
                            pass
                        print("new_product_price: " + str(new_product_price))
                        print("new_delivery_price: " + str(new_delivery_price))
                        print("used_product_price: " + str(used_product_price))
                        print("used_delivery_price: " + str(used_delivery_price))
                        print()
                        print()
                        print()
                        driver.quit()
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
                                new_delivery_price = re.findall("\d+\.\d+", results2["data-csa-c-delivery-price"])[0]
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
                            new_delivery_price = re.findall("\d+\.\d+",results2)[0]
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

                    # print(counter)

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

                                # print(counter)

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
                            try:
                                if "£" in new_product_price:
                                    new_product_price = re.findall("\d+\.\d+", new_product_price)[0]
                            except:
                                # new_product_price isn't a string
                                pass
                            print("new_product_price: " + str(new_product_price))
                            print("new_delivery_price: " + str(new_delivery_price))
                            print("used_product_price: " + str(used_product_price))
                            print("used_delivery_price: " + str(used_delivery_price))
                            print()
                            print()
                            print()
                            driver.quit()
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
                    #print(e)

                    try:
                        pass
                    except Exception as e:
                        driver.quit()
                        continue

                # Normal Secondary FOR USED PRICE
                URL = "https://www.amazon.co.uk/dp/" + str(isbn)
                driver.get(URL)
                html = driver.page_source
                soup = BeautifulSoup(html, features="lxml")

                try:
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

        print()
        try:
            if "£" in new_product_price:
                new_product_price = re.findall("\d+\.\d+", new_product_price)[0]
        except:
            # new_product_price isn't a string
            pass
        print("new_product_price: " + str(new_product_price))
        print("new_delivery_price: " + str(new_delivery_price))
        print("used_product_price: " + str(used_product_price))
        print("used_delivery_price: " + str(used_delivery_price))
        print()
        print()
        print()

        driver.quit()
    return True

def ebay_historical_prices(isbn, condition):

    if condition.lower()=="new":
        URL = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
            isbn) + "&_sacat=0&LH_Sold=1&LH_Complete=1&LH_PrefLoc=1&rt=nc"
        print(URL)
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
                    except Exception as e:
                        print(e)
                        historical_new_product_price = sum/2
                except Exception as e:
                    print(e)
                    historical_new_product_price = sum/1
            except Exception as e:
                print(e)
                historical_new_product_price = -999

            print("Historical New Product Price: £" + str(historical_new_product_price))

        except Exception as e:
            print(e)
            new_product_price = -999
            print("Historical New Product Price: FAIL")







    elif condition.lower()=="used":
        URL = "https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=" + str(
            isbn) + "&_sacat=0&LH_ItemCondition=4&LH_Sold=1&LH_Complete=1&rt=nc&LH_PrefLoc=1"
        print(URL)
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
                        print(e)
                        historical_used_product_price = sum/2
                        return historical_used_product_price
                except Exception as e:
                    print(e)
                    historical_used_product_price = sum/1
                    return historical_used_product_price
            except Exception as e:
                print(e)
                historical_used_product_price = -999
                return historical_used_product_price

            print("Historical Used Product Price: £" + str(historical_used_product_price))

        except Exception as e:
            print(e)
            used_product_price = -999
            print("Historical Used Product Price: FAIL")
            return used_product_price

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
            print("New Delivery Price: £0.00")
        else:
            new_delivery_price = re.findall("\d+\.\d+", new_delivery_price_with_sign)[0]
            print("New Delivery Price: £" + str(new_delivery_price))
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
                print("New Delivery Price: £0.00")
            else:
                # https://www.tutorialspoint.com/Extract-decimal-numbers-from-a-string-in-Python#:~:text=To%20extract%20decimal%20numbers%20from,to%20work%20with%20regular%20expressions.
                new_delivery_price = re.findall("\d+\.\d+", new_delivery_price_with_sign)[0]
                print("New Delivery Price: £" + str(new_delivery_price))
        except Exception as e:
            new_delivery_price = -999
            print("New Delivery Price: FAIL")
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
            print("Used Delivery Price: £0.00")
        else:
            used_delivery_price = re.findall("\d+\.\d+", used_delivery_price_with_sign)[0]
            print("Used Delivery Price: £" + str(used_delivery_price))
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
                print("Used Delivery Price: £0.00")
            else:
                # https://www.tutorialspoint.com/Extract-decimal-numbers-from-a-string-in-Python#:~:text=To%20extract%20decimal%20numbers%20from,to%20work%20with%20regular%20expressions.
                used_delivery_price = re.findall("\d+\.\d+", used_delivery_price_with_sign)[0]
                print("Used Delivery Price: £" + str(used_delivery_price))
        except Exception as e:
            used_delivery_price = -999
            print("Used Delivery Price: FAIL")
    return used_delivery_price


def main():
    #check_amazon_prices_today_proper_test("./scraped_database_data_amazon.csv", only_create_new_books=False)
    isbn = "0857504797"
    print(round(ebay_historical_prices(isbn,"used"),2))


if __name__ == "__main__":
    main()