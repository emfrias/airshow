from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    topic = Column(String, nullable=True)
    # Add other user-specific fields as needed

    location = relationship("LastLocation", uselist=False, back_populates="user")
    notifications = relationship('Notification', back_populates='user')
    filters = relationship('Filter', back_populates='user')

class LastLocation(Base):
    __tablename__ = 'last_locations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    alt = Column(Float, nullable=False)
    reported_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    user = relationship("User", back_populates="location")

class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, nullable=False)
    aircraft_hex = Column(String(10), nullable=False)
    notification_text = Column(Text, nullable=False)
    filter_name = Column(String, nullable=False)

    user = relationship('User', back_populates='notifications')

class Filter(Base):
    __tablename__ = 'filters'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    evaluation_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="filters")
    conditions = relationship("Condition", back_populates="filter", cascade="all, delete-orphan")


class Condition(Base):
    __tablename__ = 'conditions'
    id = Column(Integer, primary_key=True)
    filter_id = Column(Integer, ForeignKey('filters.id'), nullable=False)
    condition_type = Column(String, nullable=False)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filter = relationship("Filter", back_populates="conditions")
