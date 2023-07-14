from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
# Initialising the database
db = SQLAlchemy(app)
app.app_context().push()

# Creating the database model
class Test(db.Model):
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

@app.route("/form", methods=["POST"])
def form():
    first_name = request.form.get("first_name")
    last_name = request.form.get("surname")
    email_address = request.form.get("email_address")

    if not first_name or not last_name or not email_address:
        error_statement = "All form fields required!"
        return render_template("contact.html", error_statement=error_statement, first_name=first_name,
                               last_name=last_name, email_address=email_address)

    return render_template("form.html", first_name=first_name, last_name=last_name, email_address=email_address)

if __name__ == "__main__":
    app.run()