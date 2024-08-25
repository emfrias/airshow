import os
import logging
import requests
import time
from flask import Flask, request, jsonify
import psycopg2
from closest_approach import closest_approach, predict_future_position, compute_angle_above_horizon

# Constants
MAX_SPEED_KTS = 500  # Max speed of aircraft in knots
PREDICT_MINUTES = 3  # Predict 3 minutes into the future
EARTH_RADIUS_NM = 3440.07  # Earth's radius in nautical miles

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

# PostgreSQL connection (update with your credentials)
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

def update_users_from_db():
    print('updating user from db')
    cursor.execute("SELECT id, topic, lat, lon, alt_feet, min_distance, min_angle FROM users JOIN last_locations USING (id)")
    print('executed')
    rows = cursor.fetchall()
    print(rows)
    users = {}
    for row in rows:
        print('got user')
        users[row[0]] = {
            "topic": row[1],
            "lat": row[2],
            "lon": row[3],
            "alt": row[4],
            "min_distance": row[5],
            "angle": row[6]
        }
    return users

def update_user_location(user_id, lat, lon, alt):
    cursor.execute("UPDATE last_locations SET lat=%s, lon=%s, alt_feet=%s WHERE id=(SELECT id FROM users WHERE username=%s)", (lat, lon, alt, user_id))
    conn.commit()

def get_aircraft_data(user):
    distance_nm = MAX_SPEED_KTS * PREDICT_MINUTES / 60  # Max distance aircraft could travel in PREDICT_MINUTES
    url = f"https://opendata.adsb.fi/api/v2/lat/{user['lat']}/lon/{user['lon']}/dist/{distance_nm}"
    logger.debug(f"Fetching aircraft data for user {user['topic']} with URL: {url}")
    response = requests.get(url)
    response.raise_for_status()
    return response.json().get('aircraft', [])

def process_aircraft_for_user(user, aircraft_list):
    notifications = []
    for aircraft in aircraft_list:
        if aircraft.get('alt_baro') == 'ground':
            logger.debug(f"Skipping aircraft {aircraft['hex']} on the ground")
            continue

        if 'alt_geom' not in aircraft:
            logger.debug(f"Skipping aircraft {aircraft['hex']} with no alt_geom (potentially on the ground)")
            # Comment: We might want to compensate alt_baro with the local altimeter setting in the future
            continue

        try:
            ac_data = {
                "lat": aircraft['lat'],
                "lon": aircraft['lon'],
                "alt": aircraft['alt_geom'],
                "gs": aircraft['gs'],
                "track": aircraft['track'],
                "desc": aircraft['desc'],
                "hex": aircraft['hex']
            }
        except KeyError as e:
            logging.error(f"Error parsing aircraft data: {aircraft}")
            continue

        future_position = predict_future_position(
            ac_data['lat'], ac_data['lon'], ac_data['alt'],
            ac_data['gs'], ac_data['track'], PREDICT_MINUTES
        )

        closest_point, t_closest, min_distance = closest_approach(
            user['lat'], user['lon'], user['alt'],
            ac_data['lat'], ac_data['lon'], ac_data['alt'],
            future_position[0], future_position[1], future_position[2]
        )

        if min_distance <= user['min_distance']:
            angle = compute_angle_above_horizon(
                (user['lat'], user['lon'], user['alt']),
                closest_point
            )
            if angle > user['angle']:
                notification = {
                    "user": user['topic'],
                    "description": ac_data['desc'],
                    "hex": ac_data['hex'],
                    "time_to_closest": t_closest * PREDICT_MINUTES * 60,  # seconds to closest approach
                    "bearing": ac_data['track'],  # Simplification: Bearing as track
                    "distance": min_distance
                }
                notifications.append(notification)
                logger.info(f"Notifying {user['topic']} about {ac_data['desc']} at distance {min_distance:.2f} miles")
    return notifications

@app.route('/pub', methods=['POST'])
def receive_location():
    data = request.json
    if data.get('_type') != 'location':
        return '', 204

    user_id = request.headers.get('X-Limit-U')
    if user_id is None:
        logger.warning("No user ID provided in headers")
        return '', 400

    lat = data['lat']
    lon = data['lon']
    alt = data['alt'] * 3.281  # Convert meters to feet

    update_user_location(user_id, lat, lon, alt)
    logger.debug(f"Updated location for user {user_id}: lat={lat}, lon={lon}, alt={alt}")

    return jsonify([]), 200

def main():
    users = update_users_from_db()

    while True:
        logger.debug('here')
        for user_id, user in users.items():
            logger.debug('there')
            aircraft_list = get_aircraft_data(user)
            notifications = process_aircraft_for_user(user, aircraft_list)
            for notification in notifications:
                # Send the notification using ntfy.sh
                ntfy_url = f"https://ntfy.sh/{user['topic']}"
                message = f"Aircraft {notification['description']} is approaching: " \
                          f"{notification['distance']:.2f} miles away, " \
                          f"{notification['time_to_closest']:.0f} seconds to closest approach, " \
                          f"bearing {notification['bearing']:.1f} degrees."
                response = requests.post(ntfy_url, data=message.encode('utf-8'))
                if response.status_code == 200:
                    logger.info(f"Sent notification to {user['topic']}")
                else:
                    logger.error(f"Failed to send notification to {user['topic']}: {response.status_code}")

        time.sleep(60)

if __name__ == '__main__':
    # Start Flask app in a separate thread
    from threading import Thread
    thread = Thread(target=lambda: app.run(port=7878, host="0.0.0.0"))
    thread.start()

    # Start the main loop
    main()
