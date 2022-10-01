from app import db
from datetime import datetime
import enum



# User Schema
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    slack_id = db.Column(db.String(50), nullable=False, unique=True)
    im_channel = db.Column(db.String(50), unique=True) # D0420PRB3BL
    active = db.Column(db.Boolean, default=False, nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    welcome = db.relationship('WelcomeMessage', backref='users', lazy=True)
    messages = db.relationship('RatingMessage', backref='users', lazy=True)
    scheduled_msgs = db.relationship('ScheduledMessage', backref='users', lazy=True)
    ratings = db.relationship('Rating', backref='users', lazy=True)
    activity = db.relationship('ActivitySummary', backref='users', lazy=True)

    def __init__(self,**kwargs) -> None:
        super().__init__(**kwargs)
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f'<User {self.id} | SlackId {self.slack_id}>'
    
    def set_user_active(self):
        self.active = True
        self.date_active = datetime.utcnow()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 


# Welcome Message Schema
class WelcomeMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date_sent = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    im_channel = db.Column(db.String(50), nullable=False, unique=True)
    reaction = db.Column(db.Boolean, default=False, nullable=False)
    
    welcome_object = db.Column(db.PickleType(), nullable=True) # https://docs.sqlalchemy.org/en/14/core/type_basics.html#sqlalchemy.types.PickleType

    def __init__(self,**kwargs) -> None:
        super().__init__(**kwargs)
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f'<WelcomeMessage {self.id} | User {self.user_id}>'
    
    def set_reaction_true(self):
        self.reaction = True



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 


# Activity Summary Schema
class ScheduledMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    im_channel = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.String(50), nullable=True)
    scheduled_message_id = db.Column(db.String(100), nullable=False, unique=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    message_object = db.Column(db.PickleType(), nullable=True) # https://docs.sqlalchemy.org/en/14/core/type_basics.html#sqlalchemy.types.PickleType

    def __init__(self,**kwargs) -> None:
        super().__init__(**kwargs)
        db.session.add(self)
        db.session.commit()
        
    def __repr__(self):
        return f'<ActivitySummary {self.id} | User {self.user_id} | URL {self.img_url}>'



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 


# Rating Message Schema
class RatingMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reaction = db.Column(db.Boolean, default=False, nullable=False)
    # rating_id = db.Column(db.Integer, db.ForeignKey('rating.id'))
    rating = db.relationship('Rating', backref='rating_message', lazy=True)
    rating_queue = db.Column(db.String(50), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, nullable=True)

    message_object = db.Column(db.PickleType(), nullable=True) # https://docs.sqlalchemy.org/en/14/core/type_basics.html#sqlalchemy.types.PickleType

    def __init__(self,**kwargs) -> None:
        super().__init__(**kwargs)
        db.session.add(self)
        db.session.commit()
        
    def __repr__(self):
        return f'<RatingMessage {self.id} | User {self.user_id} | MessageObj {self.message_object}>'
    
    def set_reaction_true(self):
        self.reaction = True


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 


# Enum Type
class RatingTypes(enum.Enum):
    smile = 'Great'
    slightly_smiling_face = 'Good'
    neutral_face = 'Okay'
    slightly_frowning_face = 'Bad'
    white_frowning_face = 'Awful'

# Rating Schema
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Enum(RatingTypes), nullable=False)
    # rating_messages = db.relationship('RatingMessage', backref='rating', lazy=True)
    rating_message_id = db.Column(db.Integer, db.ForeignKey('rating_message.id'))
    modified = db.Column(db.Boolean, default=False, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self,**kwargs) -> None:
        super().__init__(**kwargs)
        db.session.add(self)
        db.session.commit()
        
    def __repr__(self):
        return f'<Rating {self.id} | User {self.user_id} | Rating {self.rating.value}>'


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 


# Activity Summary Schema
class ActivitySummary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    img_url = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, nullable=True)

    def __init__(self,**kwargs) -> None:
        super().__init__(**kwargs)
        db.session.add(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<ActivitySummary {self.id} | User {self.user_id} | URL {self.img_url}>'

    def update_date(self):
        self.date_updated = datetime.utcnow()