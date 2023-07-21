# Tutorial on creating Python Flask app from scratch, using html, bootstrap and css for frontend. SQLlite for frontend.
# https://www.youtube.com/playlist?list=PLCC34OHNcOtqJBOLjXTd5xC0e-VD3siPn

# Using Postgresql
# https://stackabuse.com/using-sqlalchemy-with-flask-and-postgresql/


from flask import Flask, render_template, request, redirect, copy_current_request_context
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import smtplib
from email.message import EmailMessage
import os
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
# https://stackoverflow.com/questions/38111620/python-isbn-13-digit-validate
import isbnlib
from ScrapingFunctionality import check_ebay_prices_today, check_amazon_prices_today
import threading

app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:password@localhost:5432/BookArbitrage"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["database_connection_string"]
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
    used_product_price = db.Column(db.Numeric(5, 2), nullable=False)
    used_delivery_price = db.Column(db.Numeric(5, 2), nullable=False)
    used_total_price = db.Column(db.Numeric(5, 2), nullable=False)

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
    used_product_price = db.Column(db.Numeric(5, 2), nullable=False)
    used_delivery_price = db.Column(db.Numeric(5, 2), nullable=False)
    used_total_price = db.Column(db.Numeric(5, 2), nullable=False)

    def __init__(self, book_name, ebay_link, isbn, edition_format, new_product_price, new_delivery_price, new_total_price,
                 used_product_price, used_delivery_price, used_total_price):
        self.book_name = book_name
        self.ebay_link = ebay_link
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/query_database")
def query_database():
    return render_template("query_database.html")
@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/books", methods =['POST','GET'])
def books():
    if updatable_amazon and updatable_ebay:
        updatable = True
    else:
        updatable = False

    if request.method == "POST":
        books = Amazon.query.order_by(Amazon.book_name)
        return render_template("books.html", books=books, updatable=updatable)
    else:
        books = Amazon.query.order_by(Amazon.book_name)
        return render_template("books.html", books=books, updatable=updatable)

@app.route("/add_books", methods =['POST','GET'])
def add_books():
    if request.method == "POST":
        book_name = request.form['book_name']
        isbn = request.form['isbn']
        ebay_link = request.form['ebay_link']
        ebay_product_price = request.form['ebay_product_price']
        ebay_delivery_price = request.form['ebay_delivery_price']
        ebay_total_price = request.form['ebay_total_price']
        amazon_link = request.form['amazon_link']
        amazon_product_price = request.form['amazon_product_price']
        amazon_delivery_price = request.form['amazon_delivery_price']
        amazon_total_price = request.form['amazon_total_price']

        # Validate Book Name
        if len(book_name) == 0:
            error_statement = "Please enter a book name!"
            return render_template("add_books.html", error_statement=error_statement, book_name=book_name, isbn=isbn,
                                   ebay_link=ebay_link, ebay_product_price=ebay_product_price,
                                   ebay_delivery_price=ebay_delivery_price, ebay_total_price=ebay_total_price,
                                   amazon_link=amazon_link, amazon_product_price=amazon_product_price,
                                   amazon_delivery_price=amazon_delivery_price, amazon_total_price=amazon_total_price)

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
            books = Amazon.query.order_by(Amazon.book_name)
            return render_template("add_books.html", error_statement=error_statement, book_name=book_name, isbn=isbn,
                                   ebay_link=ebay_link, ebay_product_price=ebay_product_price,
                                   ebay_delivery_price=ebay_delivery_price, ebay_total_price=ebay_total_price,
                                   amazon_link=amazon_link, amazon_product_price=amazon_product_price,
                                   amazon_delivery_price=amazon_delivery_price, amazon_total_price=amazon_total_price)

        # Push to database
        try:
            new_book = Amazon(book_name=book_name, isbn=isbn, amazon_link="placeholder_link", product_price=5.00,
                              delivery_price=0.00, total_price=5.00)
            db.session.add(new_book)
            db.session.commit()

            new_book = Ebay(book_name=book_name, isbn=isbn, ebay_link="placeholder_link", product_price=5.00,
                            delivery_price=0.00, total_price=5.00)
            db.session.add(new_book)
            db.session.commit()
            return redirect('/books')
        except IntegrityError:
            db.session.rollback()
            error_statement = "That book already exists in the database, " \
                              "or there is another cause for an integrity error."
            books = Amazon.query.order_by(Amazon.book_name)
            return render_template("add_books.html", error_statement=error_statement)
        except:
            db.session.rollback()
            error_statement = "There was an error adding that book to the database."
            books = Amazon.query.order_by(Amazon.book_name)
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
        with app.app_context():
            check_amazon_prices_today("./scraped_database_data_amazon.csv", only_create_new_books=False)
        print('Threaded task for updating Amazon DB has been completed')
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

    t_amazon = UpdateAmazonDB()
    t_amazon.start()

    books = Amazon.query.order_by(Amazon.book_name)
    if updatable_amazon and updatable_ebay:
        updatable = True
    else:
        updatable = False
    return redirect('/books')

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
        books = Amazon.query.order_by(Amazon.book_name)
        error_statement = "Update should include valid ISBN-10/ISBN-13 number"
        if updatable_amazon and updatable_ebay:
            updatable = True
        else:
            updatable = False
        return render_template("books.html", error_statement=error_statement, books=books, updatable=updatable)

    if request.method == "POST":
        if request.form.get('book_name'):
            book_to_update_amazon.book_name=request.form['book_name']
            book_to_update_ebay.book_name = request.form['book_name']
        if request.form.get('isbn'):
            book_to_update_amazon.isbn=request.form['isbn']
            book_to_update_ebay.isbn = request.form['isbn']

        if request.form.get('amazon_link'):
            book_to_update_amazon.total_price=request.form['amazon_link']
        if request.form.get('amazon_product_price'):
            book_to_update_amazon.total_price=request.form['amazon_product_price']
        if request.form.get('amazon_delivery_price'):
            book_to_update_amazon.total_price=request.form['amazon_delivery_price']
        if request.form.get('amazon_total_price'):
            book_to_update_amazon.total_price=request.form['amazon_total_price']

        if request.form.get('ebay_link'):
            book_to_update_ebay.total_price=request.form['ebay_link']
        if request.form.get('ebay_product_price'):
            book_to_update_ebay.total_price=request.form['ebay_product_price']
        if request.form.get('ebay_delivery_price'):
            book_to_update_ebay.total_price=request.form['ebay_delivery_price']
        if request.form.get('ebay_total_price'):
            book_to_update_ebay.total_price=request.form['ebay_total_price']

        # Push to database
        try:
            db.session.commit()
        except:
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
        return "There was a problem deleting that book from the Amazon table."

    book_to_delete = Ebay.query.get_or_404(isbn)
    try:
        db.session.delete(book_to_delete)
        db.session.commit()
    except:
        return "There was a problem deleting that book from the Ebay table."

    return redirect('/books')


@app.route("/form", methods=["POST"])
def form():
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

    return render_template("form.html", name=name, email_address=email_address, message=message)

if __name__ == "__main__":
    db.create_all()
    app.run()