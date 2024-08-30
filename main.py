import time
from flask import Flask
from api import app  # Import the Flask app from api.py
from db import update_users_from_db, get_location_for_user, update_user_location
from aircraft import get_aircraft_data, process_aircraft_for_user
from config import Session, logger
from models import User, Notification, Filter, Condition
import requests
import location_api
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

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
            # Create the user
            user = User(
                email="foo@bar.com",
                password_hash=generate_password_hash('baz'),
                topic='private_airshow_foo_bar_com'
            )

            # Create a filter for the user
            filter = Filter(
                user=user,
                name="3D Distance and Angle Alert",
                order=1
            )

            # Add conditions to the filter
            condition_3d_distance = Condition(
                filter=filter,
                condition_type='3d_distance',
                value={"max_distance": 3.0}
            )

            condition_angle_above_horizon = Condition(
                filter=filter,
                condition_type='angle_above_horizon',
                value={"min_angle": 20.0}
            )

            # Add everything to the session
            session.add(user)
            session.add(filter)
            session.add(condition_3d_distance)
            session.add(condition_angle_above_horizon)

            # Commit the transaction
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
                notifications = process_aircraft_for_user(session, user, location, aircraft_list)
                if user.topic:
                    for notification in notifications:
                        if should_send_notification(session, user, notification['hex']):
                            message = f"Aircraft {notification['description']} is approaching: " \
                                      f"{notification['distance']:.2f} miles away, " \
                                      f"{notification['time_to_closest']:.0f} seconds to closest approach, " \
                                      f"bearing {notification['bearing']:.1f} degrees."
                            send_notification(session, user, notification['hex'], message)
                else:
                    logger.debug(f"Not sending notifications for user {user.email} because they have no topic set")

            # Sleep for a while before the next loop iteration
            time.sleep(60)  # Adjust the sleep time as needed

if __name__ == '__main__':
    # Start Flask server in a separate thread
    from threading import Thread
    flask_thread = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 7878})
    flask_thread.start()

    # Start the main monitoring loop
    main()
