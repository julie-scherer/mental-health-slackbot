import logging
# logging.basicConfig(level=logging.DEBUG)


# Import the Slack Bolt app and SDK client
# https://github.com/slackapi/bolt-python
# https://github.com/slackapi/python-slack-sdk
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


# Import Flask and SQLAlchemy
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session #Session


# Import SlackRequestHandler to translate WSGI requests to 
# Bolt's interface and build WSGI response from Bolt's response.
# Source: https://slack.dev/bolt-python/concepts#adapters
# https://github.com/slackapi/bolt-python/blob/main/examples/flask/app.py
from slack_bolt.adapter.flask import SlackRequestHandler


# Specify .env path and load global variables 
import os
from dotenv import load_dotenv
load_dotenv()


# Initializes the Bolt app with the bot token and signing secret
app = App(
    token=os.environ.get("SLACK_TOKEN"), 
    signing_secret=os.environ.get("SIGNING_SECRET"),
    ignoring_self_events_enabled=False)
client = WebClient(os.environ.get("SLACK_TOKEN"))


# Initialize Flask app factory
flask_app = Flask(__name__)


# Base class declarations ! Import models here
from . import models


# Initialize Flask scoped database engine and session 
engine = create_engine(os.environ.get('DATABASE_URL'))
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


# Event handling ! Add Bolt app functionality here
from . import slack_events


# Attach the slack_bolt app to the flask app handler
handler = SlackRequestHandler(app)


# Declare the flask routes where slack will post a request ! Add Flask app routes here
from . import flask_routes


# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))