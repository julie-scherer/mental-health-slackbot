**IMPORTANT NOTE: This app is still in development mode. Some features may not work properly.** This app was first created using the Slack event adapter to handle API calls. It's currently being reconfigured to use Bolt instead. The routes have been updated but not how the events are handled. I'm working offline to modify the logic/workflow to better utilize Bolt's features. I will update the repository and README as soon as app development is complete. Many thanks for your understanding and patience!


# Ambience Slack App

## Steps to Create and Install Slack App

**Step 1**: Create Slack App at api.slack.com

**Step 2**: Add permissions (navigate to Bot Token Scopes in OAuth & Permissions tab)

**Step 3**: Install Slack App to workspace

**Step 4**: Create app dir and virtual environment (example code below)

        % mkdir slack-app
        % cd slack-app
        % python3 -m venv venv
        % . venv/bin/activate

**Step 5**: Configure the local environment with the app's credentials
  
- 5.1: Get Bot User's Access Token from OAuth & Permissions tab
  
- 5.2: Install and import slackclient, python-dotenv, and pathlib packages

        % pip3 install slackclient
        % pip3 install python-dotenv
        % pip3 install pathlib
    
- 5.3: Create .env file in local root dir (this is where you will store the token)

        >>> SLACK_TOKEN=xoxb-your_bots_token

- 5.4: Create app.py file and add the following:

        >>> import slack
        >>> import os
        >>> from pathlib import Path
        >>> from dotenv import load_dotenv

        >>> env_path = Path('.') / '.env'
        >>> load_dotenv(dotenv_path=env_path)
        >>> client = slack.WebClient(token=os.environ.get('SLACK_TOKEN'))

    _https://api.slack.com/start/building/bolt-python#credentials_
    _https://api.slack.com/start/building/bolt-python#initialize_

#### _Alas, we begin developing the app_

**Step 6**: Install Flask and initalize Flask Application Factory

        % pip3 install Flask
        
        >>> from flask import Flask
        >>> app = Flask(__name__)
        ...
        >>> if __name__ == '__main__':
        >>>     app.run(debug=True)

**Step 7**: Use ngrok as local proxy
        
- 7.1: Type the following command in the terminal to run ngrok on port 5000

        % ngrok http 5000

    _See https://ngrok.com/download for more info_

**Step 8**: Enable Events

- 8.1: Turn on events in Event Subscriptions tab
    
- 8.2: Add Request URL, which will be the ngrok forwarding address followed by 'slack/events'

    _Note ngrok URL will expire after 2 hours and every time you restart ngrok, it will generate a new URL that you will have to update as the Request URL_

- 8.3: Subscribe bot to message.channels (under Subscribe to Bot Events in Event Subscriptions tab)
    
    This will automatically add the channels:history scope for you and then you need to reinstall the app to your workspace

    _Note anytime you add an event listener, you need to make sure your bot is subscribed to that type of event and reinstall the app_

**Step 9**: Create Slack Events Adapter for handling Slack's Events API

- 9.1: Get your App's Signing Secret (from App Credentials in Basic Information tab),
            which verifies that incoming requests are coming from Slack
    
- 9.2: Save the Client Secret value as SLACK_SIGNING_SECRET in .env file
        
        >>> SLACK_SIGNING_SECRET=xoxb-your_apps_signing_secret

- 9.3: Install and import slackeventsapi

        % pip install slackeventsapi
        >>> from slackeventsapi import SlackEventAdapter

- 9.4: Create a Slack Event Adapter with 'slack/events' endpoint in app.py
        
        >>> ...
        >>> signing_secret=os.environ.get('SLACK_SIGNING_SECRET')
        >>> slack_event_adapter = SlackEventAdapter(signing_secret, '/slack/events', app)

    _Note the slack event adapter must come BEFORE the slack client is instantiated but after creating the flask app factory_

- 9.5: Create an event listener for 'message' events

        >>> @slack_event_adapter.on('message')
        >>> def message(payLoad):
        >>>     ...


**Check out these sources for more information!**
- https://slack.dev/python-slackclient/basic_usage.html#sending-a-message
- https://slack.dev/node-slack-sdk/reference/events-api
- https://api.slack.com/events
- https://github.com/slackapi/python-slack-events-api


## App development workflow

![Alt text](img/SlackAppWorkflow.png?raw=true "App Workflow")


## What does the bot do?

![Alt text](img/Slide1.png?raw=true "App Demo")
![Alt text](img/Slide2.png?raw=true "App Demo")
![Alt text](img/Slide3.png?raw=true "App Demo")
![Alt text](img/Slide4.png?raw=true "App Demo")
![Alt text](img/Slide5.png?raw=true "App Demo")
![Alt text](img/Slide6.png?raw=true "App Demo")
