import os
from dotenv import load_dotenv
from flask import request
from app import app
from slack import WebClient


load_dotenv()

CLIENT_ID = os.environ.get('CLIENT_ID')
OATH_SCOPE = os.environ.get('SLACK_SCOPES')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


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


# Tokens & Installation Source: https://python-slackclient.readthedocs.io/en/latest/auth.html