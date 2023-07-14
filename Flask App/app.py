# https://www.youtube.com/playlist?list=PLCC34OHNcOtqJBOLjXTd5xC0e-VD3siPn

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import smtplib
from email.message import EmailMessage
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///friends.db"
# Initialising the database
db = SQLAlchemy(app)
app.app_context().push()

# Creating the database model
class Friends(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # Create function to return string when we add something
    def __repr__(self):
        return "<Name %r>" % self.id


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

@app.route("/friends", methods =['POST','GET'])
def friends():
    if request.method == "POST":
        friend_name = request.form['name']
        new_friend = Friends(name=friend_name)
        # Push to database
        try:
            db.session.add(new_friend)
            db.session.commit()
            return redirect('/friends')
        except:
            return "There was an error adding the friend to the database"
    else:
        friends = Friends.query.order_by(Friends.date_created)
        return render_template("friends.html", friends=friends)

@app.route("/update/<int:id>", methods =['POST','GET'])
def update(id):
    friend_to_update = Friends.query.get_or_404(id)
    if request.method == "POST":
        friend_to_update.name=request.form['name']
        # Push to database
        try:
            db.session.commit()
            return redirect('/friends')
        except:
            return "There was an error updating that friend in the database"
    else:
        return render_template("update.html", friend_to_update=friend_to_update)

@app.route("/delete/<int:id>")
def delete(id):
    friend_to_delete = Friends.query.get_or_404(id)
    try:
        db.session.delete(friend_to_delete)
        db.session.commit()
        return redirect('/friends')
    except:
        return "There was a problem deleting that friend"


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
    server.login("bookarbitragedevteam@gmail.com",os.getenv('BookArbitrage'))

    # https://stackoverflow.com/questions/7232088/python-subject-not-shown-when-sending-email-using-smtplib-module
    msg = EmailMessage()
    msg.set_content("Name:\n" + name + "\n\n" + "Email address:\n" + email_address + "\n\n" + "Message:\n" + message)
    msg['Subject'] = "BookArbitrage Contact Form Submission"
    msg['From'] = "bookarbitragedevteam@gmail.com"
    msg['To'] = "tsoomal@hotmail.co.uk"
    server.send_message(msg)

    return render_template("form.html", name=name, email_address=email_address, message=message)

if __name__ == "__main__":
    app.run()