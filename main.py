import time
from flask import Flask
from api import app  # Import the Flask app from api.py
from db import update_users_from_db, get_location_for_user, update_user_location
from aircraft import get_aircraft_data, process_aircraft_for_user
from config import Session, logger
from models import User, Notification
import requests
import location_api
from datetime import datetime, timedelta

from datetime import datetime, timedelta

def should_send_notification(session, user, aircraft_hex):
    fifteen_minutes_ago = datetime.utcnow() - timedelta(minutes=15)

    recent_notifications = session.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.aircraft_hex == aircraft_hex,
        Notification.timestamp >= fifteen_minutes_ago
    ).count()

    return recent_notifications == 0

def send_notification(session, user, aircraft_hex, notification_text):
    # Insert the notification into the database
    new_notification = Notification(
        user_id=user.id,
        timestamp=datetime.utcnow(),
        aircraft_hex=aircraft_hex,
        notification_text=notification_text
    )
    session.add(new_notification)
    session.commit()

    # Send the notification using ntfy.sh
    ntfy_url = f"https://ntfy.sh/{user.topic}"
    response = requests.post(ntfy_url, data=notification_text.encode('utf-8'))
    if response.status_code == 200:
        logger.info(f"Sent notification to {user.topic}")
    else:
        logger.error(f"Failed to send notification to {user.topic}: {response.status_code}")

def main():
    with Session() as session:
        if not session.query(User).filter_by(email="foo@bar.com").first():
            session.add(User(email="foo@bar.com", password_hash='', topic='private_airshow_foo_bar_com', min_distance=3.0, min_angle=20.0))
            session.commit()
        while True:
            # Update users from the database
            users = update_users_from_db(session)

            # Fetch and process aircraft data for each user
            for user in users:
                location = get_location_for_user(session, user)
                if not location:
                    logger.debug(f"No location on file for user {user.email}, skipping")
                    continue
                aircraft_list = get_aircraft_data(user, location)
                notifications = process_aircraft_for_user(user, location, aircraft_list)
                for notification in notifications:
                    if should_send_notification(session, user, notification['hex']):
                        message = f"Aircraft {notification['description']} is approaching: " \
                                  f"{notification['distance']:.2f} miles away, " \
                                  f"{notification['time_to_closest']:.0f} seconds to closest approach, " \
                                  f"bearing {notification['bearing']:.1f} degrees."
                        send_notification(session, user, notification['hex'], message)

            # Sleep for a while before the next loop iteration
            time.sleep(60)  # Adjust the sleep time as needed

if __name__ == '__main__':
    # Start Flask server in a separate thread
    from threading import Thread
    flask_thread = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 7878})
    flask_thread.start()

    # Start the main monitoring loop
    main()
