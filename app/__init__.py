import os

from dotenv import load_dotenv

from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
from app.config import Config

from slack import WebClient
from slackeventsapi import SlackEventAdapter

import ssl
import certifi


# Specify .env path and load global variables 
load_dotenv()

# Slack API Tokens
# P.S. Bot OAuth Access Token is under OAuth & Permissions at api.slack.com
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
SIGNING_SECRET = os.environ.get('SIGNING_SECRET')


# Create Flask App
app = Flask(__name__)


# Configure SQLite Database
app.config.from_object(Config)


# Integrate Database to Flask App
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Initialize Slack Client
slack_events_adapter = SlackEventAdapter(SIGNING_SECRET, '/slack/events', app)  # note you will need to add /slack/events endpoint to request URL in Event Subscriptions
# client = WebClient(SLACK_TOKEN)
ssl_context = ssl.create_default_context(cafile=certifi.where())
client = WebClient(SLACK_TOKEN, ssl=ssl_context)


from . import routes, slackapi, models