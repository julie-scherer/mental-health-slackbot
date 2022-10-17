# Import packages
from sqlalchemy import Column, ForeignKey, Integer, Table, String, Boolean, DateTime, Enum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()



# User Schema
class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True)
    slack_id = Column(String(50), nullable=False, unique=True)
    im_channel = Column(String(50), unique=True) # D0420PRB3BL
    active = Column(Boolean, default=False, nullable=False)
    date_added = Column(DateTime, nullable=False, default=datetime.utcnow)
    # date_active = Column(DateTime, nullable=True)
    
    rating_messages = relationship('RatingMessage', backref='users', lazy=True)
    ratings = relationship('Rating', backref='users', lazy=True)

    def __repr__(self):
        return f'<User {self.id} | SlackId {self.slack_id}>'
    
    def set_user_active(self):
        self.active = True
        # self.date_active = datetime.utcnow()



# Rating Message Schema
class RatingMessage(Base):
    __tablename__ = "rating_message"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    channel = Column(String(50), nullable=False)
    post_at = Column(String(50), nullable=False)
    scheduled_message_id = Column(String(100), nullable=False, unique=True)
    timestamp = Column(String(50), default='')
    reaction = Column(Boolean, default=False)
    rating_queue = Column(String(50), nullable=True, default=None)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_sent = Column(DateTime, nullable=True)
    date_update_chat = Column(DateTime, nullable=True)
    date_expired = Column(DateTime, nullable=True)
    
    rating = relationship('Rating', backref='rating_message', lazy=True)
        
    def __repr__(self):
        return f'<RatingMessage {self.id} | User {self.user_id}>'
    
    def set_reaction_true(self):
        self.reaction = True

    def clear_queue(self):
        self.rating_queue = None
        


# Rating Schema
class RatingTypes(enum.Enum):
    smile = 'Great'
    slightly_smiling_face = 'Good'
    neutral_face = 'Okay'
    slightly_frowning_face = 'Bad'
    white_frowning_face = 'Awful'

class Rating(Base):
    __tablename__ = "rating"
    
    id = Column(Integer, primary_key=True)
    rating = Column(Enum(RatingTypes), nullable=False)
    rating_message_id = Column(Integer, ForeignKey('rating_message.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    modified = Column(Boolean, default=False, nullable=True)
    date_added = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_modified = Column(DateTime, nullable=True)
        
    def __repr__(self):
        return f'<Rating {self.id} | User {self.user_id} | Rating {self.rating.value}>'
    
    def change_rating(self, rating):
        self.rating = rating
        self.modified = True
        self.date_modified = datetime.utcnow()    
