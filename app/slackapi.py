from app import app, db
from app.models import ScheduledMessage, User, RatingMessage, WelcomeMessage, Rating
from config import SLACK_TOKEN, SIGNING_SECRET
from flask import Response
import datetime

import slack
from slackeventsapi import SlackEventAdapter


slack_events_adapter = SlackEventAdapter(SIGNING_SECRET, '/slack/events', app)  # note you will need to add /slack/events endpoint to request URL in Event Subscriptions
client = slack.WebClient(SLACK_TOKEN)



'''
Getting the user started
'''
#   -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

# **************************************************************
# **************** MEMBER JOINED CHANNEL TRIGGER ***************
# **************************************************************

@slack_events_adapter.on('member_joined_channel')
def member_joined_channel(event_data):
    print('member joined channel!')

    event = event_data['event']
    slack_id = event['user']
    
    response = client.users_info(user=slack_id)
    user = response['user']
    
    is_bot = user['is_bot']
    if is_bot:
        print('A bot joined the channel')
        return Response('A bot joined the channel')

    user_in_database = User.query.filter_by(slack_id=slack_id).first()
    if not user_in_database:
        profile = user['profile']
        display_name = profile['display_name']
        first_name = profile['first_name']
        email = profile['email']

        name = display_name if display_name != '' else first_name
        new_user = User(slack_id=slack_id, name=name, email=email)
        
        send_welcome_message(name=name, slack_id=slack_id, channel_id=slack_id)
        
    return



# **************************************************************
# ****************** SEND WELCOME MESSAGE FUNC *****************
# **************************************************************

# * Welcome message object *
# - - - - - - - - - - - - - -
class WelcomeMessageObj(object):
    def __init__(self, name, user, channel):
        self.name = name
        self.user = user
        self.channel = channel
        self.timestamp = ''
        self.thread_ts = ''
        # self.completed = False
    
    def get_message(self):
        START_TEXT = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': f"Hi {self.name}! I'm Ambience. I will be checking in on you every morning to see how you're feeling.\n"
            }
        }
        INSTRUCTIONS = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': (
                "It's pretty simple. All you have to is react to the message with one of these emojis!\n:smile: = 'Great!'  |  :slightly_smiling_face: = 'Good'  |  :neutral_face: = 'Okay'  |  :slightly_frowning_face: = 'Bad'  |  :white_frowning_face: = 'Awful'\n"
                "\nYou can respond at any time throughout the day. You just have to reply before the day is over if you want me to save your response. If you can't check in, that's okay. We'll start fresh the next day! :blush:\n"
                "\n_To get a summary of all your reactions, simply send 'get-summary'. As long as you've reacted to one of my messages before, you will get your summary in no time!_"
                )
            }
        }
        GET_STARTED = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': "Now let's get started! What time would you like me to check in?"
            }
        }
        DIVIDER = {'type': 'divider'}
        return {
            'ts': self.timestamp,
            'channel': self.channel,
            'text': f"Hi {self.name}! I'm Ambience. I will be checking in on you every morning to see how you're feeling.",
            'blocks': [
                START_TEXT,
                INSTRUCTIONS
                # DIVIDER
                # GET_STARTED,
            ]
        }


def send_welcome_message(name, slack_id, channel_id):
    print('sending welcome message!')

    # Create WelcomeMessageObj object
    welcome_message = WelcomeMessageObj(name=name, user=slack_id, channel=channel_id)  
    message = welcome_message.get_message()     # get welcome message
    response = client.chat_postMessage(**message)   # send message

    welcome_message.thread_ts = response['ts']  # set timestamp
    welcome_message.channel = channel_id        # set channel

    user = User.query.filter_by(slack_id=slack_id).first()    # find the user_id stored in db
    user.im_channel = response['channel'] 
    db.session.commit()

    new_welcome_message = WelcomeMessage(user_id=user.id, im_channel=channel_id, welcome_object=welcome_message)     # add data to WelcomeMessage table in db

    schedule_rating_message(name=name, user_id=user.id, channel_id=channel_id)



'''
Catching, scheduling, and replying to rating messages
'''
#   -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

# **************************************************************
# ******************* SCHEDULE RATING MESSAGE ******************
# **************************************************************

# * Rating message object *
# - - - - - - - - - - - - - -
class RatingMessageObj(object):
    def __init__(self, name, channel, post_at) -> None:
        self.name = name
        self.channel = channel
        self.post_at = post_at
        self.scheduled_message_id = ''
        self.timestamp = ''
        self.reaction = False
    
    def get_message(self):
        START_TEXT = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': f'Good morning, {self.name}! How are you feeling today?'
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
            'text': f'Good morning, {self.name}! How are you feeling today?',
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



def schedule_rating_message(name, user_id, channel_id):
    print('scheduling rating message!')
    
    # --------------------------------- TESTING & DEVELOPMENT ---------------------------------
    # test_scheduled_time = datetime.time(hour=datetime.datetime.now().hour,
    #               minute=(datetime.datetime.now() + datetime.timedelta(seconds=60)).minute,
    #               second=(datetime.datetime.now() + datetime.timedelta(seconds=60)).second
    #               )
    # test_schedule_timestamp = datetime.datetime.combine(datetime.date.today(), test_scheduled_time).strftime('%s')
    # schedule_timestamp = test_schedule_timestamp
    # -----------------------------------------------------------------------------------------

    # Create a timestamp
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    scheduled_time = datetime.time(hour=9, minute=30)
    schedule_timestamp = datetime.datetime.combine(tomorrow, scheduled_time).strftime('%s')
    
    scheduled_rating_message = RatingMessageObj(name=name, channel=channel_id, post_at=schedule_timestamp)
    message = scheduled_rating_message.get_message()
    
    # Send scheduled message
    response = client.chat_scheduleMessage(**message) 
    scheduled_rating_message.scheduled_message_id = response['scheduled_message_id']

    ScheduledMessage(scheduled_message_id=scheduled_rating_message.scheduled_message_id, 
                    user_id=user_id,
                    im_channel=response['channel'], 
                    message_object=scheduled_rating_message
                )

    return




# **************************************************************
# ********************** ON EVENT, MESSAGE *********************
# **************************************************************

import re
@slack_events_adapter.on('message')
def message(event_data):
    print('message event triggered!')

    event = event_data.get('event')

    # Set base case
    if event.get('subtype') or event.get('channel_type') != 'im':
        print('subtype message')
        return
    
    BOT_ID = client.api_call('auth.test').get('user_id')
    channel = event.get('channel')
    timestamp = event.get('ts')
    slack_id = event.get('user')
    text = event.get('text')
    user = User.query.filter_by(im_channel=channel).first() # get the user in this instant message channel
    user_ratings = Rating.query.filter_by(user_id=user.id) # get the user's ratings

    # First, we will look for rating messages sent by the bot
    if slack_id == BOT_ID:
        # Check if the sent message text sent matches the rating message text
        pattern = '^[Good morning\,]*[\w.-]+\! [How are you feeling today\?]+'
        match = re.match(pattern, text)
        if match:
            print(f'this is the bot rating message. match: {match}')
            # Get the scheduled message object from the database
            scheduled_msg = ScheduledMessage.query.filter_by(user_id=user.id).order_by(ScheduledMessage.id.desc()).first()
            # Add the delivered message timestamp to the table
            scheduled_msg.timestamp = timestamp

            # Create copy of the message object and update its attributes with the delivered message info
            delivered_rating_message = scheduled_msg.message_object
            delivered_rating_message.timestamp = timestamp
            delivered_rating_message.channel = channel

            # Now that we know the scheduled message delivered, add rating message to the database
            RatingMessage(user_id=user.id, timestamp=timestamp, message_object=delivered_rating_message)
            
            # Schedule next rating message
            schedule_rating_message(name=user.name, user_id=user.id, channel_id=channel)
        return
    
    # Now, we can ignore any messages from a bot or human who isn't in the database
    if not user:
        return
    
    # Next, we want to catch any 'get-summary' messages sent by the user
    # Check the message's slack_id is the user's and that the user has ratings in the database
    if text == 'get-summary' and slack_id == user.slack_id and user_ratings:
        # Call the get rating summary function
        summary_msg = get_rating_summary(user_ratings=user_ratings, channel=channel)
        # Send the message
        post_summary = client.chat_postMessage(**summary_msg)
        return

    # Lastly...
    # We need to get the thread_ts key from the slack API conversations_replies
    # method to get the rating message data from the database, if it exists
    response = client.conversations_replies(channel=channel, ts=timestamp)
    thread_ts = response['messages'][0].get('thread_ts')
    if thread_ts is None:
        return
    rating_message = RatingMessage.query.filter_by(timestamp=thread_ts).first()
    if not rating_message:
        return
    rating_queue = rating_message.rating_queue
    if rating_queue == 'NULL':
        return
    
    # Now that we know there is a reaction waiting in the rating message queue,
    # we can get the rating stored in the database using the rating message ID 
    rating = Rating.query.filter_by(rating_message_id=rating_message.id).first()
    # If the user said 'yes' they want to change their rating, update data in database
    if text.lower() == 'yes':
        rating.rating = rating_queue
        rating.modified = True
        rating.date = datetime.datetime.utcnow()
        rating_message.date_updated = datetime.datetime.utcnow()
        rating_message.rating_queue = 'NULL'
        db.session.commit()
        return client.chat_postMessage(channel=channel, thread_ts=timestamp, text="You got it! I've updated your response :saluting_face:")
    # If the user said 'no' they do NOT want to change their rating, remove the reaction from the queue
    elif text.lower() == 'no':
        rating_message.rating_queue = 'NULL'
        db.session.commit()
        return client.chat_postMessage(channel=channel, thread_ts=timestamp, text="No problem! Consider it forgotten :wink:")
    # Send error message if the user replied with anything other than 'yes' or 'no'
    else:
        client.chat_postMessage(channel=channel, thread_ts=timestamp, text="I'm sorry, I only understand 'yes' and 'no' :disappointed: Can you please try again?")




# **************************************************************
# *********************** REACTION ADDED ***********************
# **************************************************************

reaction_events = []
@slack_events_adapter.on('reaction_added')
def rating_message_reaction(event_data):
    print('reaction added')
    # print(json.dumps(event_data, indent=2))

    event = event_data.get('event')
    emoji = event.get('reaction')
    channel_id = event.get('item').get('channel')
    slack_id = event.get('user')
    timestamp = event.get('item').get('ts')
    
    # Check that the message reacted to is a rating message in the database
    all_sent_messages = ScheduledMessage.query.all()
    if timestamp not in {message.timestamp for message in all_sent_messages}:
        print('not rating message')
        return

    # Get the user ID and rating message object corresponding to the timestamp from database
    user_id = User.query.filter_by(slack_id=slack_id).first().id
    rating_msg = RatingMessage.query.filter_by(timestamp=timestamp).first()
    
    # Check that the message was sent within the past 24 hours
    date_created = rating_msg.date_created
    time_passed = datetime.datetime.utcnow() - date_created     # date_created = datetime.datetime.strptime(date_created, '%Y-%m-%d %H:%M:%S.%f')
    time_allocated = datetime.timedelta(hours=24)          
    # time_allocated = datetime.timedelta(seconds=60) # FOR DEVELOPMENT
    if time_passed > time_allocated:
        client.chat_postMessage(channel=channel_id, thread_ts=timestamp, text="I'm sorry, it's too late to react to this message.")
        return 

    accepted_reacts = ['smile', 'slightly_smiling_face', 'neutral_face', 'slightly_frowning_face', 'white_frowning_face']
    if emoji not in accepted_reacts:
        client.chat_postMessage(channel=channel_id, thread_ts=timestamp, text="Hmm. I'm not sure I understand. Are you sure you selected the correct emoji?")
        return
    
    # Check that a reaction has NOT been added to the rating message (default is false)
    if rating_msg.reaction is False:
        # Get the rating message object from the database and set reaction attribute to true
        rating_message = rating_msg.message_object
        rating_message.reaction = True

        # Call the get message method and update chat
        message = rating_message.get_message()
        client.chat_update(**message)
        
        # Call the set reaction true method in database and commit changes
        rating_msg.set_reaction_true()
        db.session.commit()

        # Add the rating to the database
        new_rating = Rating(user_id=user_id, rating=emoji, rating_message_id=rating_msg.id)

    # If the rating message already HAS a reaction, add the reaction to the queue 
    # and catch the user's reply via the 'on message trigger' (see above) 
    else:
        rating = Rating.query.filter_by(rating_message_id=rating_msg.id).first()
        rating_msg.rating_queue = emoji
        rating.rating_queue = emoji
        db.session.commit()
        client.chat_postMessage(channel=channel_id, thread_ts=timestamp, text=f"You already responded to this message. Are you sure you want to update your reaction? Reply yes/no")




# **************************************************************
# ******************* GET RATING SUMMARY FUNC ******************
# **************************************************************

def get_rating_summary(user_ratings, channel):
    text = ''
    for user_rating in user_ratings:
        rating_name = user_rating.rating.name
        value = user_rating.rating.value
        date = user_rating.date
        formatted_date = datetime.datetime.strftime(date, "%a %d-%b")
        text += f"{formatted_date}\t:arrow_right:\t:{rating_name}:  {value}\n"
    
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
            'text': text
        }        
    }    
    return {
        'channel': channel,
        'type': 'mrkdwn',
        'text': "You got it, boss! All your ratings are listed below.",
        'blocks': [
            START_TEXT,
            DIVIDER,
            RATING_TEXT
        ]        
    }
