import logging

# logging.basicConfig(level=logging.DEBUG)


# Specify .env path and load global variables 
import os
from dotenv import load_dotenv
load_dotenv()


# Initializes app with bot token and signing secret
from slack_bolt import App
slack_app = App(
    token=os.environ.get("SLACK_TOKEN"),
    signing_secret=os.environ.get("SIGNING_SECRET")
)

from slack_sdk import WebClient
client = WebClient(os.environ.get("SLACK_TOKEN"))


# Bolt middleware
@slack_app.middleware
def log_request(logger, body, next):
    logger.debug(body)
    return next()



# Initialize Flask app
from flask import Flask, request
flask_app = Flask(__name__)

# Configure SQLite database
from . import config
flask_app.config.from_object(config.Config)

# Integrate Database to Flask App
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
from flask_cors import CORS
CORS(flask_app)
db = SQLAlchemy(flask_app)
migrate = Migrate(flask_app, db)


# SlackRequestHandler translates WSGI requests to Bolt's interface and builds WSGI response from Bolt's response
# Source: https://slack.dev/bolt-python/concepts#adapters
from slack_bolt.adapter.flask import SlackRequestHandler
handler = SlackRequestHandler(slack_app)


# Register routes to Flask app
from . import slack_events, flask_routes, models