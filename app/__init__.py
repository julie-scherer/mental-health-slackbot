from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
from config import Config

# Create Flask App
app = Flask(__name__)

# Configure SQLite Database
app.config.from_object(Config)

# Integrate Database to Flask App
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Example of Flask route
@app.route('/')
def hello():
    return render_template("index.html")

from . import slackapi, models

