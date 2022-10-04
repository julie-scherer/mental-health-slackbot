import os

from pathlib import Path
from dotenv import load_dotenv

from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
from app.config import Config

from slack import WebClient
from slackeventsapi import SlackEventAdapter



# Specify .env path and load global variables 
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Slack API Tokens
# P.S. Bot OAuth Access Token is under OAuth & Permissions at api.slack.com
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
SIGNING_SECRET = os.environ.get('SIGNING_SECRET')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
OATH_TOKEN = os.environ.get('OATH_TOKEN')
OATH_SCOPE = os.environ.get('SLACK_SCOPES')


# Create Flask App
app = Flask(__name__)


# Configure SQLite Database
app.config.from_object(Config)


# Integrate Database to Flask App
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Create Slack Events Adapter and Client
slack_events_adapter = SlackEventAdapter(SIGNING_SECRET, '/slack/events', app)  # note you will need to add /slack/events endpoint to request URL in Event Subscriptions
client = WebClient(SLACK_TOKEN)


# The OAuth initiation link
@app.route("/slack/install", methods=["GET"])
def pre_install():
    return f'<a href="https://slack.com/oauth/v2/authorize?scope={OATH_SCOPE}&client_id={CLIENT_ID}">Add to Slack</a>'


# The OAuth completion page
@app.route("/slack/oauth_redirect", methods=["GET"])
def post_install():
    # Retrieve the auth code from the request params
    code_param = request.args['code']

    # An empty string is a valid token for this request
    client = WebClient()

    # Request the auth tokens from Slack
    response = client.oauth_v2_access(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        code=code_param
    )
    print(response)

    # Save the bot token to an environmental variable or to your data store for later use
    # https://api.slack.com/methods/oauth.v2.access
    os.environ["SLACK_TOKEN"] = response['access_token']

    return "Installation is completed!"


from . import slackapi, models

# Tokens & Installation Source: https://python-slackclient.readthedocs.io/en/latest/auth.html