from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    min_distance = Column(Float, nullable=False)
    min_angle = Column(Float, nullable=False)
    # Add other user-specific fields as needed

    notifications = relationship('Notification', back_populates='user')

class LastLocation(Base):
    __tablename__ = 'last_locations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    alt = Column(Float, nullable=False)
    user = relationship("User", back_populates="location")

User.location = relationship("LastLocation", uselist=False, back_populates="user")

class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, nullable=False)
    aircraft_hex = Column(String(10), nullable=False)
    notification_text = Column(Text, nullable=False)

    user = relationship('User', back_populates='notifications')
