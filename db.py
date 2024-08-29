from sqlalchemy.orm import Session
from models import User, LastLocation
from config import Session

def update_users_from_db(session):
    return session.query(User).all()

# Lookup user's current location
def get_location_for_user(session, user):
    return session.query(LastLocation).filter_by(user_id=user.id).first()

def get_user_by_email(session, email):
    return session.query(User).filter(User.email == email).first()

def get_user_by_id(session, id):
    return session.query(User).filter(User.id == id).first()

def update_user_location(session, user_id, lat, lon, alt):
    location = session.query(LastLocation).filter(LastLocation.user_id == user_id).first()
    if location:
        location.lat = lat
        location.lon = lon
        location.alt = alt
    else:
        location = LastLocation(user_id=user_id, lat=lat, lon=lon, alt=alt)
        session.add(location)
    session.commit()
