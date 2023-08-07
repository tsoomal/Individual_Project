# Tutorial on creating Python Flask app from scratch, using html, bootstrap and css for frontend. SQLlite for frontend.
# https://www.youtube.com/playlist?list=PLCC34OHNcOtqJBOLjXTd5xC0e-VD3siPn
import csv
import decimal

# Using Postgresql
# https://stackabuse.com/using-sqlalchemy-with-flask-and-postgresql/

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, create_engine
import smtplib
from email.message import EmailMessage
import os
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
# https://stackoverflow.com/questions/38111620/python-isbn-13-digit-validate
import isbnlib
import psycopg2
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import CompositeType, register_composites
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY

from ScrapingFunctionality import check_ebay_prices_today, check_amazon_prices_today, get_ebay_historical_price
import threading
from PriceModelling import storage_ebay_to_amazon, storage_amazon_to_ebay
from datetime import datetime
from collections import OrderedDict


app = Flask(__name__)
# https://stackoverflow.com/questions/65888631/how-do-i-use-heroku-postgres-with-my-flask-sqlalchemy-app
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["database_connection_string"]
engine = create_engine(os.environ['database_connection_string'])
#engine.connect()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = 'secret string'
# Initialising the database
db = SQLAlchemy(app)
app.app_context().push()
migrate = Migrate(app,db)

global updatable_amazon
updatable_amazon = True
global updatable_ebay
updatable_ebay = True

register_composites(engine.connect())

# Creating the database model
class Amazon(db.Model):
    __tablename__ = 'Amazon'
    book_name = db.Column(db.String(200), nullable=False)
    amazon_link = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(13), primary_key=True)
    edition_format = db.Column(db.String(40), nullable=False)
    new_product_price = db.Column(db.Numeric(5,2), nullable=False)
    new_delivery_price = db.Column(db.Numeric(5,2), nullable=False)
    new_total_price = db.Column(db.Numeric(5,2), nullable=False)
    used_product_price = db.Column(db.Numeric(5,2), nullable=False)
    used_delivery_price = db.Column(db.Numeric(5,2), nullable=False)
    used_total_price = db.Column(
            ARRAY(
                CompositeType(
                    'composite_type',
                    [
                        db.Column('my_datetime_column', db.TIMESTAMP),
                        db.Column('my_numeric_column', db.Numeric(5, 2))
                    ]
                ),
                dimensions=1
            )
        )

    def __init__(self, book_name, amazon_link, isbn, edition_format, new_product_price, new_delivery_price, new_total_price,
                 used_product_price, used_delivery_price, used_total_price):
        self.book_name = book_name
        self.amazon_link = amazon_link
        self.isbn = isbn
        self.edition_format = edition_format
        self.new_product_price = new_product_price
        self.new_delivery_price = new_delivery_price
        self.new_total_price = new_total_price
        self.used_product_price = used_product_price
        self.used_delivery_price = used_delivery_price
        self.used_total_price = used_total_price

    def __repr__(self):
        return f"<Book: {self.book_name}>"

class Ebay(db.Model):
    __tablename__ = 'Ebay'
    book_name = db.Column(db.String(200), nullable=False)
    ebay_link = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(13), primary_key=True)
    edition_format = db.Column(db.String(40), nullable=False)
    new_product_price = db.Column(db.Numeric(5, 2), nullable=False)
    new_delivery_price = db.Column(db.Numeric(5, 2), nullable=False)
    new_total_price = db.Column(db.Numeric(5, 2), nullable=False)
    historical_new_total_price = db.Column(db.Numeric(5, 2), nullable=False)
    used_product_price = db.Column(db.Numeric(5, 2), nullable=False)
    used_delivery_price = db.Column(db.Numeric(5, 2), nullable=False)
    used_total_price = db.Column(db.Numeric(5, 2), nullable=False)
    historical_used_total_price = db.Column(db.Numeric(5, 2), nullable=False)

    def __init__(self, book_name, ebay_link, isbn, edition_format, new_product_price, new_delivery_price,
                 new_total_price, historical_new_total_price, used_product_price, used_delivery_price, used_total_price,
                 historical_used_total_price):
        self.book_name = book_name
        self.ebay_link = ebay_link
        self.isbn = isbn
        self.edition_format = edition_format
        self.new_product_price = new_product_price
        self.new_delivery_price = new_delivery_price
        self.new_total_price = new_total_price
        self.historical_new_total_price = historical_new_total_price
        self.used_product_price = used_product_price
        self.used_delivery_price = used_delivery_price
        self.used_total_price = used_total_price
        self.historical_used_total_price = historical_used_total_price

    def __repr__(self):
        return f"<Book: {self.book_name}>"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/query_database_by_isbn/<string:isbn>")
def query_database_by_isbn(isbn):
    try:
        print("ISBN: " + isbn)
        book_amazon = Amazon.query.get_or_404(isbn)
        book_ebay = Ebay.query.get_or_404(isbn)
        return render_template("view_record_details.html",
                               book_ebay=book_ebay,
                               book_amazon=book_amazon)
    except Exception as e:
        print(e)
        return redirect('/opportunities')

@app.route("/contact")
def contact():
    try:
        # book_to_update_amazon = Amazon.query.get_or_404("1529391431")
        # print(book_to_update_amazon.amazon_link)


        # {"(2023-08-05 22:14:02,-999)"}
        ts = datetime.now()
        # print(ts)
        f = '%Y-%m-%d %H:%M:%S'
        my_timestamp = datetime.strptime(str(ts).split(".")[0], f)
        # #my_timestamp = ts.timestamp()
        print(my_timestamp)
        new_book = Amazon(book_name="test_book_1", amazon_link="amazon_link",
                              isbn=1529391432, edition_format="Paperback",
                              new_product_price=10.99,
                              new_delivery_price=0.99,
                              new_total_price=11.98,
                              used_product_price=-999,
                              used_delivery_price=-999,
                              used_total_price=-999)
        db.session.add(new_book)
        db.session.commit()
        print("Record added")
    except Exception as e:
        print(e)
        db.session.rollback()
    return render_template("contact.html")

@app.route("/contact_form", methods=["POST"])
def contact_form():
    name = request.form.get("name")
    email_address = request.form.get("email_address")
    message = request.form.get("message")

    # Error-handling
    if not name or not email_address or not message:
        error_statement = "All form fields required!"
        return render_template("contact.html", error_statement=error_statement, name=name,
                               email_address=email_address, message=message)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    # Environmental Variable has to be configured in run-time environment
    server.login("bookarbitragedevteam@gmail.com",os.getenv('gmail_password'))

    # https://stackoverflow.com/questions/7232088/python-subject-not-shown-when-sending-email-using-smtplib-module
    msg = EmailMessage()
    msg.set_content("Name:\n" + name + "\n\n" + "Email address:\n" + email_address + "\n\n" + "Message:\n" + message)
    msg['Subject'] = "BookArbitrage Contact Form Submission"
    msg['From'] = "bookarbitragedevteam@gmail.com"
    msg['To'] = "tsoomal@hotmail.co.uk"
    server.send_message(msg)

    return render_template("contact_form.html", name=name, email_address=email_address, message=message)

@app.route("/books", methods =['POST','GET'])
def books():
    if updatable_amazon and updatable_ebay:
        updatable = True
    else:
        updatable = False

    try:
        num_records_amazon = db.session.query(func.count(Amazon.isbn)).scalar()
    except Exception as e:
        print(e)
        print("num_records_amazon not found!")
        db.session.rollback()

    try:
        num_records_ebay = db.session.query(func.count(Ebay.isbn)).scalar()
    except Exception as e:
        print(e)
        print("num_records_ebay not found!")
        db.session.rollback()

    if request.method == "POST":
        try:
            books_ebay = Ebay.query.order_by(Ebay.book_name)
            books_amazon = Amazon.query.order_by(Amazon.book_name)
            return render_template("books.html", books_ebay=books_ebay, books_amazon=books_amazon, updatable=updatable,
                                   zip=zip, num_records_ebay=num_records_ebay, num_records_amazon=num_records_amazon)
        except Exception as e:
            print(e)
            error_statement = "Error with database connection. Please refresh page!"
            db.session.rollback()
            return render_template("books.html", error_statement=error_statement, zip=zip, enumerate=enumerate)
    else:
        # request.method == "GET"
        try:
            books_ebay = Ebay.query.order_by(Ebay.book_name)
            books_amazon = Amazon.query.order_by(Amazon.book_name)
            return render_template("books.html", books_ebay=books_ebay, books_amazon=books_amazon, updatable=updatable,
                                   zip=zip, num_records_ebay=num_records_ebay, num_records_amazon=num_records_amazon)
        except Exception as e:
            print(e)
            error_statement = "Error with database connection. Please refresh page!"
            db.session.rollback()
            return render_template("books.html", error_statement=error_statement, zip=zip, enumerate=enumerate)


@app.route("/add_books", methods =['POST','GET'])
def add_books():
    if request.method == "POST":
        book_name = request.form['book_name']
        isbn = request.form['isbn']
        edition_format = request.form['edition_format']
        ebay_link = request.form['ebay_link']
        ebay_new_product_price = request.form['ebay_new_product_price']
        ebay_new_delivery_price = request.form['ebay_new_delivery_price']
        ebay_new_total_price = request.form['ebay_new_total_price']
        ebay_used_product_price = request.form['ebay_used_product_price']
        ebay_used_delivery_price = request.form['ebay_used_delivery_price']
        ebay_used_total_price = request.form['ebay_used_total_price']
        amazon_link = request.form['amazon_link']
        amazon_new_product_price = request.form['amazon_new_product_price']
        amazon_new_delivery_price = request.form['amazon_new_delivery_price']
        amazon_new_total_price = request.form['amazon_new_total_price']
        amazon_used_product_price = request.form['amazon_used_product_price']
        amazon_used_delivery_price = request.form['amazon_used_delivery_price']
        amazon_used_total_price = request.form['amazon_used_total_price']

        if "www." in amazon_link:
            amazon_link = amazon_link.split("www.",1)[1]

        if "www." in ebay_link:
            ebay_link = ebay_link.split("www.",1)[1]

        # Validate Book Name
        if len(book_name) == 0:
            error_statement = "Please enter a book name!"
            return render_template("add_books.html", error_statement=error_statement, book_name=book_name, isbn=isbn,
                                   edition_format=edition_format,
                                   ebay_link=ebay_link, ebay_new_product_price=ebay_new_product_price,
                                   ebay_new_delivery_price=ebay_new_delivery_price,
                                   ebay_new_total_price=ebay_new_total_price,
                                   ebay_used_product_price=ebay_used_product_price,
                                   ebay_used_delivery_price=ebay_used_delivery_price,
                                   ebay_used_total_price=ebay_used_total_price,
                                   amazon_link=amazon_link, amazon_new_product_price=amazon_new_product_price,
                                   amazon_new_delivery_price=amazon_new_delivery_price,
                                   amazon_new_total_price=amazon_new_total_price,
                                   amazon_used_product_price=amazon_used_product_price,
                                   amazon_used_delivery_price=amazon_used_delivery_price,
                                   amazon_used_total_price=amazon_used_total_price
                                   )

        # Validate ISBN
        try:
            if len(isbn) == 10 or len(isbn) == 13:
                if len(isbn) == 10:
                    if isbnlib.is_isbn10(isbn) == True:
                        pass
                    else:
                        raise Exception
                elif len(isbn) == 13:
                    if isbnlib.is_isbn13(isbn) == True:
                        pass
                    else:
                        raise Exception
            else:
                raise Exception
        except:
            error_statement = "ISBN has to be in either ISBN-10 or ISBN-13 format!"
            return render_template("add_books.html", error_statement=error_statement, book_name=book_name,
                                   isbn=isbn, edition_format=edition_format,
                                   ebay_link=ebay_link, ebay_new_product_price=ebay_new_product_price,
                                   ebay_new_delivery_price=ebay_new_delivery_price,
                                   ebay_new_total_price=ebay_new_total_price,
                                   ebay_used_product_price=ebay_used_product_price,
                                   ebay_used_delivery_price=ebay_used_delivery_price,
                                   ebay_used_total_price=ebay_used_total_price,
                                   amazon_link=amazon_link, amazon_new_product_price=amazon_new_product_price,
                                   amazon_new_delivery_price=amazon_new_delivery_price,
                                   amazon_new_total_price=amazon_new_total_price,
                                   amazon_used_product_price=amazon_used_product_price,
                                   amazon_used_delivery_price=amazon_used_delivery_price,
                                   amazon_used_total_price=amazon_used_total_price)

        # Get historical prices
        historical_new_total_price = get_ebay_historical_price(isbn, "new")
        historical_used_total_price = get_ebay_historical_price(isbn, "used")

        # Push to database
        try:
            new_book = Amazon(book_name=book_name, amazon_link=amazon_link, isbn=isbn, edition_format=edition_format,
                              new_product_price=amazon_new_product_price,
                              new_delivery_price=amazon_new_delivery_price, new_total_price=amazon_new_total_price,
                              used_product_price=amazon_used_product_price,
                              used_delivery_price=amazon_used_delivery_price, used_total_price=amazon_used_total_price)
            db.session.add(new_book)
            db.session.commit()

            new_book = Ebay(book_name=book_name, ebay_link=ebay_link, isbn=isbn, edition_format=edition_format,
                            new_product_price=ebay_new_product_price,
                            new_delivery_price=ebay_new_delivery_price, new_total_price=ebay_new_total_price,
                            historical_new_total_price=historical_new_total_price,
                            used_product_price=ebay_used_product_price, used_delivery_price=ebay_used_delivery_price,
                            used_total_price=ebay_used_total_price,
                            historical_used_total_price=historical_used_total_price)
            db.session.add(new_book)
            db.session.commit()

            # Add to Amazon csv of books.
            data = [book_name, amazon_link, edition_format, isbn]
            with open("scraped_database_data_amazon.csv", "a+", newline="", encoding="UTF8") as f:
                writer = csv.writer(f)
                writer.writerow(data)

            # Add to Ebay csv of books.
            data = [book_name, ebay_link, edition_format, isbn]
            with open("scraped_database_data_ebay.csv", "a+", newline="", encoding="UTF8") as f:
                writer = csv.writer(f)
                writer.writerow(data)

            return redirect('/books')
        except IntegrityError:
            db.session.rollback()
            error_statement = "That book already exists in the database, " \
                              "or there is another cause for an integrity error."
            return render_template("add_books.html", error_statement=error_statement)
        except:
            db.session.rollback()
            error_statement = "There was an error adding that book to the database."
            return render_template("add_books.html", error_statement=error_statement)

    return render_template("add_books.html")


# https://unbiased-coder.com/python-flask-multithreading/#How_To_Background_Task_In_Flask
class UpdateAmazonDB(threading.Thread):
    def __init__(self):
        super(UpdateAmazonDB, self).__init__()
    def run(self):
        # https://stackoverflow.com/questions/73999854/flask-error-runtimeerror-working-outside-of-application-context
        # https://realpython.com/python-use-global-variable-in-function/#:~:text=If%20you%20want%20to%20modify,built%2Din%20globals()%20function
        globals()["updatable_amazon"] = False
        try:
            with app.app_context():
                check_amazon_prices_today("./scraped_database_data_amazon.csv", only_create_new_books=False)
                #check_amazon_prices_today("./scraped_database_data_amazon.csv", only_create_new_books=True)

                # NEED TO ADD COLUMN FOR DAY LAST UPDATED.
                # status = check_amazon_prices_today("./scraped_database_data_amazon.csv", only_create_new_books=False)
                # while status == False:
                #     status = check_amazon_prices_today("./scraped_database_data_amazon.csv",
                #                                        only_create_new_books=True)

            print('Threaded task for updating Amazon DB has been completed')
            globals()["updatable_amazon"] = True
        except:
            print('Threaded task for updating Amazon DB has FAILED')
            globals()["updatable_amazon"] = True
class UpdateEbayDB(threading.Thread):
    def __init__(self):
        super(UpdateEbayDB, self).__init__()
    def run(self):
        # https://stackoverflow.com/questions/73999854/flask-error-runtimeerror-working-outside-of-application-context
        globals()["updatable_ebay"] = False
        with app.app_context():
            check_ebay_prices_today("./scraped_database_data_ebay.csv", only_create_new_books=False)
        print('Threaded task for updating Ebay DB has been completed')
        globals()["updatable_ebay"] = True

@app.route("/update_prices_in_database")
def update_prices_in_database():
    # https://stackoverflow.com/questions/62435134/how-to-run-a-function-in-background-without-blocking-main-thread-and-serving-fla

    t_ebay = UpdateEbayDB()
    t_ebay.start()

    #t_amazon = UpdateAmazonDB()
    #t_amazon.start()

    return redirect('books')

@app.route("/update/<string:isbn>", methods =['POST','GET'])
def update(isbn):
    book_to_update_amazon = Amazon.query.get_or_404(isbn)
    book_to_update_ebay = Ebay.query.get_or_404(isbn)

    try:
        if request.form.get('isbn'):
            isbn = request.form.get('isbn')
            if len(isbn) == 10:
                if isbnlib.is_isbn10(isbn) == True:
                    pass
                else:
                    raise Exception
            elif len(isbn) == 13:
                if isbnlib.is_isbn13(isbn) == True:
                    pass
                else:
                    raise Exception
    except:
        error_statement = "Update should include valid ISBN-10/ISBN-13 number"
        if updatable_amazon and updatable_ebay:
            updatable = True
        else:
            updatable = False
        num_records_amazon = db.session.query(func.count(Amazon.isbn)).scalar()
        num_records_ebay = db.session.query(func.count(Ebay.isbn)).scalar()
        books_ebay = Ebay.query.order_by(Ebay.book_name)
        books_amazon = Amazon.query.order_by(Amazon.book_name)
        return render_template("books.html", books_ebay=books_ebay, books_amazon=books_amazon, updatable=updatable,
                               zip=zip, num_records_ebay=num_records_ebay, num_records_amazon=num_records_amazon,
                               error_statement=error_statement)

    if request.method == "POST":
        if request.form.get('book_name'):
            book_to_update_amazon.book_name=request.form['book_name']
            book_to_update_ebay.book_name = request.form['book_name']
        if request.form.get('isbn'):
            book_to_update_amazon.isbn=request.form['isbn']
            book_to_update_ebay.isbn = request.form['isbn']

        if request.form.get('amazon_link'):
            book_to_update_amazon.amazon_link=request.form['amazon_link']
        if request.form.get('amazon_new_product_price'):
            book_to_update_amazon.new_product_price=request.form['amazon_new_product_price']
        if request.form.get('amazon_new_delivery_price'):
            book_to_update_amazon.new_delivery_price=request.form['amazon_new_delivery_price']
        if request.form.get('amazon_new_total_price'):
            book_to_update_amazon.new_total_price=request.form['amazon_new_total_price']
        if request.form.get('amazon_used_product_price'):
            book_to_update_amazon.used_product_price = request.form['amazon_used_product_price']
        if request.form.get('amazon_used_delivery_price'):
            book_to_update_amazon.used_delivery_price = request.form['amazon_used_delivery_price']
        if request.form.get('amazon_used_total_price'):
            book_to_update_amazon.used_total_price = request.form['amazon_used_total_price']

        if request.form.get('ebay_link'):
            book_to_update_ebay.ebay_link = request.form['ebay_link']
        if request.form.get('ebay_new_product_price'):
            book_to_update_ebay.new_product_price = request.form['ebay_new_product_price']
        if request.form.get('ebay_new_delivery_price'):
            book_to_update_ebay.new_delivery_price = request.form['ebay_new_delivery_price']
        if request.form.get('ebay_new_total_price'):
            book_to_update_ebay.new_total_price = request.form['ebay_new_total_price']
        if request.form.get('ebay_used_product_price'):
            book_to_update_ebay.used_product_price = request.form['ebay_used_product_price']
        if request.form.get('ebay_used_delivery_price'):
            book_to_update_ebay.used_delivery_price = request.form['ebay_used_delivery_price']
        if request.form.get('ebay_used_total_price'):
            book_to_update_ebay.used_total_price = request.form['ebay_used_total_price']

        book_to_update_ebay.historical_new_total_price= get_ebay_historical_price(isbn, "new")
        book_to_update_ebay.historical_used_total_price = get_ebay_historical_price(isbn, "used")

        # Push to database
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return "There was an error updating that book in the database"
    else:
        return render_template("update.html", book_to_update=book_to_update_amazon,
                               book_to_update_ebay=book_to_update_ebay, book_to_update_amazon=book_to_update_amazon)

    return redirect('/books')

@app.route("/delete/<string:isbn>")
def delete(isbn):
    book_to_delete = Amazon.query.get_or_404(isbn)
    try:
        db.session.delete(book_to_delete)
        db.session.commit()
    except:
        db.session.rollback()
        return "There was a problem deleting that book from the Amazon table."

    book_to_delete = Ebay.query.get_or_404(isbn)
    try:
        db.session.delete(book_to_delete)
        db.session.commit()
    except:
        db.session.rollback()
        return "There was a problem deleting that book from the Ebay table."

    return redirect('/books')

@app.route("/delete_all_books")
def delete_all_books():
    # https://stackoverflow.com/questions/16573802/flask-sqlalchemy-how-to-delete-all-rows-in-a-single-table
    try:
        num_rows_deleted = db.session.query(Amazon).delete()
        print("Number of rows deleted from Amazon Table: " + str(num_rows_deleted))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("ERROR: No rows deleted from Amazon Table.")
        print(e)

    try:
        num_rows_deleted = db.session.query(Ebay).delete()
        print("Number of rows deleted from Ebay Table: " + str(num_rows_deleted))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("ERROR: No rows deleted from Ebay Table.")
        print(e)

    return redirect('/books')

@app.route("/opportunities")
def opportunities():

    try:
        all_books_ebay = Ebay.query.order_by(Ebay.book_name)
        all_books_amazon = Amazon.query.order_by(Amazon.book_name)

        books_amazon_new = []
        books_ebay_new = []
        books_amazon_used = []
        books_ebay_used = []
        profit_new = []
        profit_used = []
        # ADD PROFIT
        # ADD LINKS
        # BUY NEW, SELL USED BOOKS

        for book_ebay, book_amazon in zip(all_books_ebay, all_books_amazon):

            # NEW BOOKS
            if book_ebay.new_total_price == -999 and book_amazon.new_total_price == -999:
                # No arbitrage possible
                pass
            elif book_ebay.new_total_price == -999 and book_amazon.new_total_price != -999:
                # Buy on Amazon, Sell on Ebay
                # Need to get historical average sold price on eBay.
                pass
            elif book_ebay.new_total_price != -999 and book_amazon.new_total_price == -999:
                # Buy on Ebay, Sell on Amazon
                pass
            elif book_ebay.new_total_price > book_amazon.new_total_price:
                # Buy on Amazon, Sell on Ebay
                total_selling_price_to_breakeven = (storage_amazon_to_ebay(book_amazon.new_total_price))
                if book_ebay.new_total_price < book_ebay.historical_new_total_price:
                    if book_ebay.new_total_price > total_selling_price_to_breakeven:
                        books_amazon_new.append(book_amazon)
                        books_ebay_new.append(book_ebay)
                        profit_new.append(book_ebay.new_total_price-book_amazon.new_total_price)
                elif book_ebay.new_total_price > book_ebay.historical_new_total_price:
                    if book_ebay.historical_new_total_price > total_selling_price_to_breakeven:
                        books_amazon_new.append(book_amazon)
                        books_ebay_new.append(book_ebay)
                        profit_new.append(round(decimal.Decimal(book_ebay.historical_new_total_price),2)-book_amazon.new_total_price)

            elif book_ebay.new_total_price < book_amazon.new_total_price:
                # Buy on Ebay, Sell on Amazon
                total_selling_price_to_breakeven = (storage_ebay_to_amazon(book_ebay.new_total_price))
                if book_amazon.new_total_price > total_selling_price_to_breakeven:
                    books_amazon_new.append(book_amazon)
                    books_ebay_new.append(book_ebay)
                    profit_new.append(book_amazon.new_total_price - book_ebay.new_total_price)
            else:
                # Both books have the same new total prices.
                pass

            # USED BOOKS
            if book_ebay.used_total_price == -999 and book_amazon.used_total_price == -999:
                # No arbitrage possible
                pass
            elif book_ebay.used_total_price == -999 and book_amazon.used_total_price != -999:
                # Buy on Amazon, Sell on Ebay
                # Need to get historical average sold price on eBay.
                pass
            elif book_ebay.used_total_price != -999 and book_amazon.used_total_price == -999:
                # Buy on Ebay, Sell on Amazon
                pass
            elif book_ebay.used_total_price > book_amazon.used_total_price:
                # Buy on Amazon, Sell on Ebay
                total_selling_price_to_breakeven = (storage_amazon_to_ebay(book_amazon.used_total_price))
                if book_ebay.used_total_price < book_ebay.historical_used_total_price:
                    if book_ebay.used_total_price > total_selling_price_to_breakeven:
                        books_amazon_used.append(book_amazon)
                        books_ebay_used.append(book_ebay)
                        profit_used.append(book_ebay.used_total_price - book_amazon.used_total_price)
                elif book_ebay.used_total_price > book_ebay.historical_used_total_price:
                    if book_ebay.historical_used_total_price > total_selling_price_to_breakeven:
                        books_amazon_used.append(book_amazon)
                        books_ebay_used.append(book_ebay)
                        profit_used.append(round(decimal.Decimal(book_ebay.historical_used_total_price),2) - book_amazon.used_total_price)
            elif book_ebay.used_total_price < book_amazon.used_total_price:
                # Buy on Ebay, Sell on Amazon
                total_selling_price_to_breakeven = (storage_ebay_to_amazon(book_ebay.used_total_price))
                if book_amazon.used_total_price > total_selling_price_to_breakeven:
                    books_amazon_used.append(book_amazon)
                    books_ebay_used.append(book_ebay)
                    profit_used.append(book_amazon.used_total_price - book_ebay.used_total_price)
            else:
                # Both books have the same used total prices.
                pass

                # # BUY NEW, SELL USED BOOKS
                # if book_ebay.new_total_price == -999 and book_amazon.new_total_price == -999:
                #     # No arbitrage possible
                #     pass
                # elif book_ebay.new_total_price == -999 and book_amazon.new_total_price != -999:
                #     # Buy on Amazon, Sell on Ebay
                #     # Need to get historical average sold price on eBay.
                #     pass
                # elif book_ebay.new_total_price != -999 and book_amazon.new_total_price == -999:
                #     # Buy on Ebay, Sell on Amazon
                #     pass
                # elif book_ebay.new_total_price > book_amazon.new_total_price:
                #     # Buy on Amazon, Sell on Ebay
                #     total_selling_price_to_breakeven = (storage_amazon_to_ebay(book_amazon.new_total_price))
                #     if book_ebay.new_total_price > total_selling_price_to_breakeven:
                #         books_amazon_new.append(book_amazon)
                #         books_ebay_new.append(book_ebay)
                # elif book_ebay.new_total_price < book_amazon.new_total_price:
                #     # Buy on Ebay, Sell on Amazon
                #     total_selling_price_to_breakeven = (storage_ebay_to_amazon(book_ebay.new_total_price))
                #     if book_amazon.new_total_price > total_selling_price_to_breakeven:
                #         books_amazon_new.append(book_amazon)
                #         books_ebay_new.append(book_ebay)
                # else:
                #     # Both books have the same new total prices.
                #     pass

        number_of_new_opps = len(profit_new)
        number_of_used_opps = len(profit_used)

        sorted_lists_new = sorted(zip(books_ebay_new, books_amazon_new, profit_new), reverse=True, key=lambda x: x[2])
        books_ebay_new, books_amazon_new, profit_new = [[x[i] for x in sorted_lists_new] for i in range(3)]

        sorted_lists_used = sorted(zip(books_ebay_used, books_amazon_used, profit_used), reverse=True, key=lambda y: y[2])
        books_ebay_used, books_amazon_used, profit_used = [[y[j] for y in sorted_lists_used] for j in range(3)]

        return render_template("opportunities.html", books_amazon_new=books_amazon_new, books_ebay_new=books_ebay_new,
                               books_amazon_used=books_amazon_used, books_ebay_used=books_ebay_used, profit_new=profit_new,
                               profit_used=profit_used, zip=zip, number_of_new_opps=number_of_new_opps,
                               number_of_used_opps=number_of_used_opps)
    except:
        error_statement = "Error with connecting to database. Please refresh!"
        number_of_new_opps = 0
        number_of_used_opps = 0

        return render_template("opportunities.html", error_statement=error_statement, zip=zip, number_of_new_opps=number_of_new_opps,
                               number_of_used_opps=number_of_used_opps)

@app.route("/sync_tables")
def sync_tables():
    # https://stackoverflow.com/questions/32938475/flask-sqlalchemy-check-if-row-exists-in-table
    try:
        all_books_ebay = Ebay.query.order_by(Ebay.isbn)
        all_books_amazon = Amazon.query.order_by(Amazon.isbn)

        for book_ebay in all_books_ebay:
            isbn = book_ebay.isbn
            exists = db.session.query(db.exists().where(Amazon.isbn == isbn)).scalar()
            if exists:
                pass
            else:
                try:
                    db.session.delete(book_ebay)
                    db.session.commit()
                    print("Book deleted from Ebay table!")
                except:
                    db.session.rollback()

        for book_amazon in all_books_amazon:
            isbn = book_amazon.isbn
            exists = db.session.query(db.exists().where(Ebay.isbn == isbn)).scalar()
            if exists:
                pass
            else:
                try:
                    db.session.delete(book_amazon)
                    db.session.commit()
                    print("Book deleted from Amazon table!")
                except:
                    db.session.rollback()

    except:
        db.session.rollback()
        print("Failed to sync tables.")

    return redirect('/books')


if __name__ == "__main__":
    db.create_all()
    app.run()