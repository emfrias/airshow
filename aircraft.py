import requests
from models import LastLocation, Filter, Condition, User, Notification
from config import Session, logger, UPDATE_RATE
from closest_approach import closest_approach, predict_future_position, compute_angle_above_horizon, compute_2d_distance, calculate_bearing
from sqlalchemy.orm import joinedload

# Constants
MAX_SPEED_KTS = 500  # Max speed of aircraft in knots
PREDICT_MINUTES = 3  # Predict 3 minutes into the future
EARTH_RADIUS_NM = 3440.07  # Earth's radius in nautical miles

def get_aircraft_data(user, location, overall_max_distance):
    logger.debug(f"Fetching aircraft user {user.email}")

    # figure out what radius around the user's current location we need to ask for data about.
    # We base this on the overall_max_distance from the user's filters (i.e. the user wants
    # to be notified of aircraft coming within 10 miles of their location), then add the
    # number of miles a fast plane would be able to travel in our prediction time window.
    distance_nm = overall_max_distance + MAX_SPEED_KTS * PREDICT_MINUTES / 60
    url = f"https://opendata.adsb.fi/api/v2/lat/{location.lat}/lon/{location.lon}/dist/{distance_nm}"
    logger.debug(f"Fetching aircraft data for user {user.email} with URL: {url}")
    response = requests.get(url)
    response.raise_for_status()
    return response.json().get('aircraft', [])

# Load all active filters for the user, ordered by their evaluation order
def get_filters_for_user(session, user):
    return session.query(Filter).options(joinedload(Filter.conditions)).filter_by(user_id=user.id).order_by(Filter.evaluation_order).all()

# look at all the filters and return the max 2d/3d distance condition
# we find.
# We require each filter to have either a 2d or 3d distance condition, in
# addition to any other conditions.  The distance condition allows us to
# set a limit on how large a radius we use in our API calls requesting
# nearby planes
# Could return None for invalid filters without a distance
def get_max_distance_from_filters(filters):
    overall_max_distance = None
    for user_filter in filters:
        # Assume all conditions in the filter are met until proven otherwise
        all_conditions_met = True

        for condition in user_filter.conditions:
            # Evaluate 3D-distance condition
            if condition.condition_type == '3d_distance':
                max_distance = condition.value['max_distance']
                if overall_max_distance is None or max_distance > overall_max_distance:
                    overall_max_distance = max_distance
            # Evaluate 2D-distance condition
            elif condition.condition_type == '2d_distance':
                max_distance = condition.value['max_distance']
                if overall_max_distance is None or max_distance > overall_max_distance:
                    overall_max_distance = max_distance
    return overall_max_distance

def process_aircraft_for_user(session, user, location, aircraft_list, filters, max_filter_distance):
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
            logger.error(f"Error parsing aircraft data: {aircraft}: {e}")
            continue

        future_position = predict_future_position(
            ac_data['lat'], ac_data['lon'], ac_data['alt'],
            ac_data['gs'], ac_data['track'], PREDICT_MINUTES
        )

        closest_point, t_closest, min_distance = closest_approach(
            location.lat, location.lon, location.alt,
            ac_data['lat'], ac_data['lon'], ac_data['alt'],
            future_position[0], future_position[1], future_position[2]
        )

        t_closest_seconds = t_closest * PREDICT_MINUTES * 60
        time_cutoff = 2 * UPDATE_RATE

        if min_distance > max_filter_distance:
            logger.debug(f"☒ Aircraft {ac_data['desc']} will not come within {max_filter_distance:.2f}nm, closest approach is {min_distance:.2f}nm")
            continue
        if t_closest_seconds > 2 * UPDATE_RATE:
            # our goal is to alert for aircraft that are between 1 and 2 minutes out (1 - 2 * UPDATE_RATE).
            # If we alert for aircraft that are more than 2 minutes out, some of those aircraft may change course
            # before they're <2 minutes out and we'd alert the user for nothing.
            logger.debug(f"☐ Aircraft {ac_data['desc']} is potentially of interest, but it is still {t_closest_seconds} seconds from closest approach of {min_distance:.2f}nm.  Ignoring until it's less than {time_cutoff} seconds away")
            continue
        else:
            logger.debug(f"☑ Aircraft {ac_data['desc']} will be {min_distance:.2f}nm in {t_closest_seconds} seconds, checking user filters")

        for user_filter in filters:
            # Assume all conditions in the filter are met until proven otherwise
            all_conditions_met = True

            for condition in user_filter.conditions:
                # Evaluate 3D-distance condition
                if condition.condition_type == '3d_distance':
                    max_distance = condition.value['max_distance']
                    if not is_within_3d_distance(min_distance, max_distance):
                        all_conditions_met = False
                        break

                # Evaluate 2D-distance condition
                elif condition.condition_type == '2d_distance':
                    max_distance = condition.value['max_distance']
                    if not is_within_2d_distance(closest_point, location, max_distance):
                        all_conditions_met = False
                        break

                # Evaluate angle-above-horizon condition
                elif condition.condition_type == 'angle_above_horizon':
                    min_angle = condition.value['min_angle']
                    if not is_above_angle(closest_point, location, min_angle):
                        all_conditions_met = False
                        break

                # Evaluate altitude condition
                elif condition.condition_type == 'altitude_below':
                    max_altitude = condition.value['max_altitude']
                    if not is_below_altitude(ac_data, max_altitude):
                        all_conditions_met = False
                        break

            if all_conditions_met:
                notification = {
                    "user": user.topic,
                    "description": ac_data['desc'],
                    "hex": ac_data['hex'],
                    "time_to_closest": t_closest * PREDICT_MINUTES * 60,  # seconds to closest approach
                    "bearing": calculate_bearing(location.lat, location.lon, closest_point[0], closest_point[1]),
                    "distance": min_distance,
                    "filter_name": user_filter.name
                }
                notifications.append(notification)
                logger.info(f"Notifying {user.topic} about {ac_data['desc']} at distance {min_distance:.2f} miles")
                break # don't process any other filters for this aircraft
    return notifications

def is_within_3d_distance(distance, max_distance):
    return distance <= max_distance

def is_within_2d_distance(closest_point, location, max_distance):
    return compute_2d_distance(closest_point[0], closest_point[1], location.lat, location.lon) <= max_distance

def is_above_angle(closest_point, location, min_angle):
    angle = compute_angle_above_horizon(
        (location.lat, location.lon, location.alt),
        closest_point
    )
    return angle >= min_angle

def is_below_altitude(aircraft, max_altitude):
    return aircraft['alt'] < max_altitude


