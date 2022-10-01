import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Specify .env path and load global variables 
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Slack API Tokens - P.S. Bot OAuth Access Token is under OAuth & Permissions at api.slack.com
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET')

# SQLite Database Configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') 
    #       or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False