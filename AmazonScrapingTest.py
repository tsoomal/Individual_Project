import os
from datetime import datetime
import time
import werkzeug
import pandas as pd
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
                        driver.get_screenshot_as_file('./screenshot.png')
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
                    driver.get_screenshot_as_file('./screenshot.png')
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
                                    driver.get_screenshot_as_file('./screenshot.png')
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
                            driver.get_screenshot_as_file('./screenshot.png')
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
                        driver.get_screenshot_as_file('./screenshot.png')
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


def main():
    check_amazon_prices_today_isbn("./scraped_database_data_amazon.csv", "1804990922", only_create_new_books=False)
    print()
    print()
    check_amazon_prices_today_isbn("./scraped_database_data_amazon.csv", "185286480X",only_create_new_books=False)
    print()
    print()
    check_amazon_prices_today_isbn("./scraped_database_data_amazon.csv", "0907610900", only_create_new_books=False)
    print()
    print()
    check_amazon_prices_today_isbn("./scraped_database_data_amazon.csv", "1852868163", only_create_new_books=False)
    print()
    print()
    check_amazon_prices_today_isbn("./scraped_database_data_amazon.csv", "1780926804", only_create_new_books=False)
    print()
    print()
    check_amazon_prices_today_isbn("./scraped_database_data_amazon.csv", "1779509529", only_create_new_books=False)
    print()
    print()
    check_amazon_prices_today_isbn("./scraped_database_data_amazon.csv", "0753801523", only_create_new_books=False)


if __name__ == "__main__":
    main()


