from app import flask_app
from data.reset import clear_all_data

clear_all_data(run=True)

if __name__ == '__main__':
    flask_app.run(debug=True)

# * Glitch: https://slackbot-ambience.glitch.me/