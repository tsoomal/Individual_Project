from flask import Flask, render_template
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

@app.route("/queryDatabase")
def queryDatabase():
    return render_template("queryDatabase.html")

# @app.route("/showdb")
# def testdb():
#     title = "testdb Database"
#     return render_template("test.html", title=title)

if __name__ == "__main__":
    app.run()