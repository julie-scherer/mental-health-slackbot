# Deploying a slack_bolt app with gunicorn
# https://blog.tryfrindle.com/deploying-a-slack_bolt-app-with-gunicorn/


from app import flask_app, handler
from flask import request


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@flask_app.route("/slack/actions", methods=["POST"])
def slack_actions():
    return handler.handle(request)


@flask_app.route("/get-summary", methods=["POST"])
def get_summary_route():
    return handler.handle(request)


@flask_app.route("/slack/install", methods=["GET"])
def install():
    return handler.handle(request)


@flask_app.route("/slack/oauth_redirect", methods=["GET"])
def oauth_redirect():
    return handler.handle(request)