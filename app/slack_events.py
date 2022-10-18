# * Glitch: https://glitch.com/slackbot-ambience

import logging
from slack_sdk.errors import SlackApiError
logger = logging.getLogger(__name__)


from app.models import User, RatingMessage, Rating
from app import app, client, Session
from datetime import timedelta
import datetime
import re
import pytz

utc = pytz.UTC

BOT_ID = client.api_call("auth.test")['user_id']

SCHEDULE_HOUR = 9
SCHEDULE_MIN = 0
SCHEDULE_SEC = 0



# ! Bolt Middleware - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

@app.middleware
def log_request(body, next, logger):
    print(f"\nLog request \n{body}")
    return next()


@app.middleware
def log_message(body, next, logger):
    print(f"Log message \n{body}")
    return next()

  

# ! Object Classes - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# ** Home view display
class HomeView(object):
    def __init__(self):
        self.type = "home"
        self.callback_id = "home_view"

    # the view object that appears in the app home
    def get_view(self):
        HEADER = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Welcome to your _App's Home_* :tada:"
            }
        }

        START_TEXT = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': f"I'm Ambience. I will be checking in on you every morning to see how you're feeling.\n"
            }
        }

        DIVIDER = {'type': 'divider'}

        BODY = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': (
                    "It's pretty simple. All you have to is react to the message with one of these emojis!"
                    "\n\t:smile: = 'Great!'\n\t:slightly_smiling_face: = 'Good'\n\t:neutral_face: = 'Okay'\n\t:slightly_frowning_face: = 'Bad'\n\t:white_frowning_face: = 'Awful'\n"
                    "\nYou can respond at any time throughout the day. You just have to reply before the day is over if you want me to save your response. If you can't check in, that's okay. We'll start fresh the next day! :blush:\n"
                    "\n_To get a summary of all your reactions, simply send 'get-summary'. As long as you've reacted to one of my messages before, you will get your summary in no time!_"
                )
            }
        }

        GET_STARTED = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': "Now let's get started!"
            }
        }

        BUTTON = {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "get_started",
                    "text": {
                        "type": "plain_text",
                        "text": "Get started!"
                    }
                }
            ]
        }

        return {
            "type": self.type,
            "callback_id": self.callback_id,
            "blocks": [
                HEADER,
                DIVIDER,
                START_TEXT,
                BODY,
                DIVIDER,
                GET_STARTED,
                BUTTON
            ]

        }


# ** Rating message body/text
class RatingMessageDisplay(object):
    def __init__(self, user_id, channel, post_at, scheduled_message_id='', timestamp='', reaction=False) -> None:
        self.user_id = user_id
        self.channel = channel
        self.post_at = post_at
        self.scheduled_message_id = scheduled_message_id
        self.timestamp = timestamp
        self.reaction = reaction

    def get_message(self):
        text = f'Good morning, <@{self.user_id}>! How are you feeling today?'

        START_TEXT = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': text
            }
        }
        DIVIDER = {'type': 'divider'}
        RATING_SCALE = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': (
                    'Great = :smile:\n'
                    'Good = :slightly_smiling_face:\n'
                    'Okay = :neutral_face:\n'
                    'Bad = :slightly_frowning_face:\n'
                    'Awful = :white_frowning_face:\n'
                )
            }
        }

        return {
            'ts': self.timestamp,
            'channel': self.channel,
            'post_at': self.post_at,
            'text': text,
            'blocks': [
                START_TEXT,
                RATING_SCALE,
                DIVIDER,
                self._get_reaction()
            ]
        }

    def _get_reaction(self):
        checkmark = ':white_check_mark:'
        if not self.reaction:
            checkmark = ':white_large_square:'
        return {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': f'{checkmark} *React to this message!*'
            }
        }


# ** Get summary message body/text
class GetSummaryDisplay(object):
    def __init__(self, user_ratings, channel) -> None:
        self.user_ratings = user_ratings
        self.channel = channel

    def get_ratings(self):
        for user_rating in self.user_ratings:
            rating_name = user_rating.rating.name
            value = user_rating.rating.value
            date = user_rating.date
            formatted_date = datetime.datetime.strftime(date, "%a %d-%b")
            text += f"{formatted_date}\t:arrow_right:\t:{rating_name}:  {value}\n"
        return text

    def get_message(self):
        START_TEXT = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': "You got it, boss! All your ratings are listed below."
            }
        }
        DIVIDER = {'type': 'divider'}
        RATING_TEXT = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': self.get_ratings()
            }
        }
        return {
            'channel': self.channel,
            'type': 'mrkdwn',
            'text': "You got it, boss! All your ratings are listed below.",
            'blocks': [
                START_TEXT,
                DIVIDER,
                RATING_TEXT
            ]
        }



# ! Functions - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# ** Check message was sent by the bot
def is_bot_message(slack_id):
    if slack_id == BOT_ID:
        return True
    return False


# ** Find user
def find_user(slack_id=None, im_channel=None):
    if slack_id:
        return Session.query(User).filter_by(slack_id=slack_id).first()
    if im_channel:
        return Session.query(User).filter_by(im_channel=im_channel).first()


# ** Find rating message
def find_rating_message(timestamp=None, channel=None):
    # all_rating_messages = Session.query(RatingMessage).all()
    # and timestamp in {message.timestamp for message in all_rating_messages}
    if timestamp:
        return Session.query(RatingMessage).filter_by(timestamp=timestamp).first()
    if channel:
        return Session.query(RatingMessage).filter_by(channel=channel).order_by(RatingMessage.id.desc()).first()


# ** Find a user's rating
def get_user_ratings(user_id=None, rating_message_id=None):
    if user_id:
        return Session.query(Rating).filter_by(user_id=user_id)
    if rating_message_id:
        return Session.query(Rating).filter_by(rating_message_id=rating_message_id).first()


# ** Get a user's Slack ID from message using regex
def get_slack_id(text=None):
    # body['event']['blocks'][0]['elements'][1]['user_id']
    return re.findall("\@[\w.-]+", text)[0].strip('@')


# ** Function to create scheduled timestamp
def scheduled_datetime(hr=SCHEDULE_HOUR, min=SCHEDULE_MIN, sec=SCHEDULE_SEC):
    # Get today's datetime
    now = utc.localize(datetime.datetime.now())

    # Create datetime variable for scheduled date/time
    est = pytz.timezone('EST')
    dt = datetime.datetime(now.year, now.month, now.day, hr, min, sec, tzinfo=est)
    timestamp = dt.timestamp()
    scheduled_dt = utc.localize(datetime.datetime.fromtimestamp(timestamp))

    # If time is in the past, increment date by 1 day
    if scheduled_dt < now:
        scheduled_dt += timedelta(days=1)

    print(f"Message scheduled for {scheduled_dt}")
    return scheduled_dt


# ** Schedule rating message
def schedule_rating_message(slack_id, channel):
    print("Scheduling rating message...")

    # Check that the user exists and is active
    user = find_user(slack_id=slack_id) # Session.query(User).filter_by(slack_id=slack_id).first()
    if (not user) or (user and user.active == 'false'):
        raise Exception("User does not exist or is inactive")

    # Create timestamp
    scheduled_timestamp = scheduled_datetime().strftime('%s')

    # Create rating message object
    scheduled_message = RatingMessageDisplay(user_id=slack_id, channel=channel, post_at=scheduled_timestamp)
    message = scheduled_message.get_message()

    # Schedule message
    response = client.chat_scheduleMessage(**message)
    print("Rating message scheduled")

    # Save the channel from the scheduled message response
    channel = response['channel']

    # List scheduled messages
    ids = list_scheduled_messages(channel=channel)
    print(f"Scheduled message IDs: {ids}")
    
    # Add scheduled message to database
    rating_message = RatingMessage(
        user_id=user.id,
        channel=channel,
        post_at=scheduled_timestamp,
        scheduled_message_id=response['scheduled_message_id']
    )
    Session.add(rating_message)
    Session.commit()

    return print(f"Rating message added to database: {rating_message}")


# ** List scheduled message IDs
def list_scheduled_messages(channel=None):
    if not channel:
        return f"Channel {channel} not found"
    response = client.chat_scheduledMessages_list(channel=channel)
    messages = response.data['scheduled_messages']
    ids = set()
    for msg in messages:
        # print(msg)
        ids.add(msg['id'])
    return ids


# ** Delete all scheduled messages
def delete_scheduled_messages(channel):
    ids = list_scheduled_messages(channel)
    for id in ids:
        app.client.chat_deleteScheduledMessage(
            channel=channel, scheduled_message_id=id)
    return ids


# ** Save reaction to database
def save_react(rating_message, emoji, channel):
    user_id = rating_message.user_id
    slack_id = Session.query(User).get(user_id).slack_id
    message_id = rating_message.id

    # Reconstruct rating message and set reaction attribute to true
    update_rating_message = RatingMessageDisplay(
        user_id=slack_id,
        channel=channel,
        post_at=rating_message.post_at,
        timestamp=rating_message.timestamp,
        reaction=True
    )

    # Get message and update chat
    message = update_rating_message.get_message()
    client.chat_update(**message)

    # Update reaction to true and commit changes
    rating_message.set_reaction_true()
    rating_message.date_update_chat = datetime.datetime.utcnow()
    Session.add(rating_message)

    # Add rating to database
    rating = Rating(user_id=user_id, rating=emoji,
                    rating_message_id=message_id)

    # Commit changes
    Session.add(rating)
    Session.commit()

    return f"Rating added to database: {rating}"


# ** Add reaction to queue (if message already reacted to)
def queue_react(rating_message, emoji, channel, timestamp):
    # Add emoji to reaction queue
    rating_message.rating_queue = emoji

    # Commit changes
    Session.add(rating_message)
    Session.commit()

    # Post message
    client.chat_postMessage(channel=channel, thread_ts=timestamp, text=f"You already responded to this message. Are you sure you want to update your reaction? Reply yes/no")

    return f"Message posted: 'You already responded to this message. Are you sure you want to update your reaction? Reply yes/no'"


  
# ! Event Handling - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# https://github.com/slackapi/bolt-python

# ** Home app opened
@app.event("app_home_opened")
def update_home_tab(client, event, logger):

    print("\n'app_home_opened' event triggered")
    # print(f"Response \n{event}")

    try:
        # Get the user from the event data
        slack_id = event["user"]

        # Create HomeView object
        home_view = HomeView()

        # Get the view object that appears in the app home
        view = home_view.get_view()

        # Use views.publish() to push a view to the Home tab
        response = client.views_publish(
            # the user that opened your app's app home
            user_id=slack_id,
            # the main body of the view to display
            view={**view}
        )

        # Log the client.views_publish response (optional)
        # print(f"Home views publish \n{response}")

    except SlackApiError as e:
        logger.error(f"Error publishing home tab: {e}")

    except Exception as ex:
        logger.error(f"Exception: {ex}")


# ** "Get started" action
@app.action("get_started")
def get_started(ack, body, say, logger):
    # must acknowledge your app received the incoming event within 3 seconds
    ack()

    print("\n'get_started' action triggered")
    print(f"Response \n{body}")

    try:
        # Find user in db
        slack_id = body['user']['id']
        user = find_user(slack_id=slack_id)

        # If the user exists and is already active, do nothing
        if user and user.active == True:
            return
        # Add user if they don't exist already
        elif not user:
            new_user = User(slack_id=slack_id, im_channel='', active=True)
            Session.add(new_user)
            Session.commit()
            print(f"User added to database: {new_user}")
        # Set user active if they exist but are inactive
        else:
            user.set_user_active()
            Session.add(user)
            Session.commit()
            print(f"User now active: {user}")

        # Post a message to the chat
        text = f"Hi there, <@{slack_id}>! Let's get started!"
        say(text=text, channel=slack_id)

    except SlackApiError as e:
        logger.error(f"Error handling 'get started' action: \n{e}")

    except Exception as ex:
        logger.error(f"Exception: {ex}")


# ** Get started message
# note: regular expression matches are inside of context.matches
@app.message("Hi there, \<\@[\w.-]+\>\! Let's get started!")
def welcome_message_event(body, message, logger):

    print(
        f"\nRegEx message event triggered: 'Hi there, \<\@[\w.-]+\>\! Let's get started!'")
    print(f"Response \n{message}")

    try:
        # Check the message was sent by the bot
        if not is_bot_message(body['event']['user']):
            raise SlackApiError("Message not sent by Ambience bot", 400)

        slack_id = get_slack_id(text=body['event']['text'])
        channel = body['event']['channel']

        # Find user and update channel ID
        user = find_user(slack_id=slack_id)
        user.im_channel = channel
        Session.add(user)
        Session.commit()
        print(f"User channel updated: {user}")

        # Schedule rating message
        schedule_rating_message(slack_id=slack_id, channel=slack_id)

    except SlackApiError as e:
        logger.error(f"Error handling welcome message event: \n{e}")

    except Exception as ex:
        logger.error(f"Exception: {ex}")


# ** Rating message event
@app.message(re.compile("^[Good morning\,]* \<\@[\w.-]+\>\! [How are you feeling today\?]+"))
def rating_message_received(body, message, context, logger):

    print(
        "\nRegEx message event triggered: '^[Good morning\,]* \<\@[\w.-]+\>\! [How are you feeling today\?]+'")
    print(f"Response \n{message} \nRegEx matches: {context.matches}")

    try:
        # Check the message was sent by the bot
        if not is_bot_message(body['event']['user']):
            raise SlackApiError("Message not sent by Ambience bot", 400)

        # Get the user, message ts, and channel
        slack_id = get_slack_id(text=body['event']['text'])
        timestamp = body['event']['ts']
        channel = body['event']['channel']
        print(
            f"<slack_id = {slack_id} | timestamp = {timestamp} | channel = {channel}>")

        # Check rating message exists
        rating_message = find_rating_message(channel=channel)
        if not rating_message:
            raise Exception("Rating message not found")
        
        # Update date sent and timestamp
        rating_message.date_sent = datetime.datetime.utcnow()
        rating_message.timestamp = timestamp

        # Commit changes
        Session.add(rating_message)
        Session.commit()
        print(f"Rating message updated: {rating_message}")

        # Schedule next rating message
        schedule_rating_message(slack_id=slack_id, channel=slack_id)

    except SlackApiError as e:
        logger.error(f"Error handling rating message event: \n{e}")

    except Exception as ex:
        logger.error(f"Exception: {ex}")


# ** Reaction added event
@app.event("reaction_added")
def reaction_added(body, event, logger):

    print("\nReaction event triggered")
    print(f"Response \n{event}")

    try:
        emoji = event['reaction']
        channel = event['item']['channel']
        slack_id = event['user']
        timestamp = event['item']['ts']

        # Check the user exists
        user = find_user(slack_id=slack_id)
        if not user:
            raise Exception(f"User not found")

        # Check the message is a rating message
        rating_message = find_rating_message(timestamp=timestamp)
        if not rating_message:
            raise Exception(f"Rating message not found")

        # Check the message was sent within the past 24 hours
        if datetime.datetime.utcnow() > rating_message.date_expired:
            client.chat_postMessage(channel=channel, thread_ts=timestamp,
                                    text="I'm sorry, it's too late to react to this message.")
            return "Message posted: I'm sorry, it's too late to react to this message."

        # Check the user responded with one of the accepted emojis
        if emoji not in {'smile', 'slightly_smiling_face', 'neutral_face', 'slightly_frowning_face', 'white_frowning_face'}:
            client.chat_postMessage(channel=channel, thread_ts=timestamp,
                                    text="Hmm. I'm not sure I understand. Are you sure you selected the correct emoji?")
            return "Message posted: Hmm. I'm not sure I understand. Are you sure you selected the correct emoji?"

        reaction = rating_message.reaction

        # Check if message already has a reaction (default reaction is false)
        if reaction:
            queue_react(rating_message, emoji, channel, timestamp)
        else:
            save_react(rating_message, emoji, channel)

    except SlackApiError as e:
        logger.error(f"Error handling 'reaction added' event: \n{e}")

    except Exception as ex:
        logger.error(f"Exception: {ex}")


# ** Get summary command
@app.command("get-summary")
def get_summary(ack, respond, body, event, logger):
    # must acknowledge your app received the incoming event within 3 seconds
    ack()

    print(f"\n'get-summary' command triggered")
    print(f"Response \n{event}")

    try:
        channel = body['event']['channel']

        # Check that the user exists
        user = find_user(im_channel=channel)
        if not user:
            raise Exception(f"User not found")

        # Get the user's ratings
        user_ratings = get_user_ratings(user_id=user.id)
        if not user_ratings:
            raise Exception(f"User ratings not found")

        # Create summary message object
        summary_msg = GetSummaryDisplay(
            user_ratings=user_ratings, channel=channel)
        message = summary_msg.get_message()

        respond(**message)

    except SlackApiError as e:
        logger.error(f"Error running get-summary command: \n{e}")

    except Exception as ex:
        logger.error(f"Exception: {ex}")


# ** User replies yes/no (to changing their react/rating)
@app.message("^(?i:(Yes|Yeah|Yep|Ya|No|Nah).*)$")
def yes_no_message(body, message, context, logger):

    print(f"\nMessage event triggered: yes/no")
    print(f"Response \n{message} \nRegEx matches: {context.matches}")

    try:
        # Check the message was NOT sent by the bot
        if is_bot_message(body['event']['user']):
            return

        text = body['event']['text']
        timestamp = body['event']['thread_ts']

        rating_message = find_rating_message(timestamp=timestamp)
        if not rating_message:
            raise Exception(f"Rating message not found")

        if rating_message.rating_queue is None:
            raise Exception(f"Rating queue is empty")

        channel = rating_message.channel

        # Now that we know there is a reaction waiting in the rating message queue,
        # we can get the rating stored in the database using the rating message ID
        rating = get_user_ratings(rating_message_id=rating_message.id)

        # User replied 'yes' they want to change their rating
        if re.match("(?i)^[yes]+", text):
            # Change rating to rating queue and clear queue
            rating.change_rating(rating=rating_message.rating_queue)
            rating_message.clear_queue()

            # Commit changes
            Session.commit()

            client.chat_postMessage(channel=channel, thread_ts=timestamp,
                                    text="You got it! I've updated your response :saluting_face:")
            return "Message posted: You got it! I've updated your response :saluting_face:"

        # User replied 'no' they do not want to change their rating
        elif re.match("(?i)^[no]+", text):
            # Remove the reaction from the queue
            rating_message.clear_queue()

            # Commit changes
            Session.add(rating_message)
            Session.commit()

            client.chat_postMessage(
                channel=channel, thread_ts=timestamp, text="No problem! Consider it forgotten :wink:")
            return "Message posted: No problem! Consider it forgotten :wink:"

        # User replied with something other than 'yes' or 'no'
        else:
            client.chat_postMessage(channel=channel, thread_ts=timestamp,
                                    text="I'm sorry, I only understand 'yes' and 'no' :disappointed: Can you please try again?")
            return "Message posted: I'm sorry, I only understand 'yes' and 'no' :disappointed: Can you please try again?"

    except SlackApiError as e:
        logger.error(
            f"Error handling yes/no message or updating reaction in db: \n{e}")

    except Exception as ex:
        logger.error(f"Exception: {ex}")


# ** Catch other message events
@app.event("message")
def handles_messages(event, context):
    # print(f"Message event \n{context}")
    return "Message event triggered"
