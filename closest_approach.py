import numpy as np

# Earth's radius in feet
EARTH_RADIUS_FEET = 6371 * 3280.84  # Convert from km to feet

# Helper function to convert degrees to radians
def deg_to_rad(deg):
    return deg * np.pi / 180.0

# Helper function to convert radians to degrees
def rad_to_deg(rad):
    return rad * 180.0 / np.pi

# Haversine formula to compute the 2D distance between two lat/lon points
def haversine_distance(lat1, lon1, lat2, lon2):
    dlat = deg_to_rad(lat2 - lat1)
    dlon = deg_to_rad(lon2 - lon1)
    lat1 = deg_to_rad(lat1)
    lat2 = deg_to_rad(lat2)

    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return EARTH_RADIUS_FEET * c

# Helper function to compute the 3D distance between two points considering altitude
def compute_3d_distance(lat1, lon1, alt1, lat2, lon2, alt2):
    surface_distance = haversine_distance(lat1, lon1, lat2, lon2)
    altitude_difference = abs(alt1 - alt2)
    return np.sqrt(surface_distance**2 + altitude_difference**2)

# Function to compute the angle above the horizon
def compute_angle_above_horizon(user_pos, aircraft_pos):
    horizontal_distance = haversine_distance(user_pos[0], user_pos[1], aircraft_pos[0], aircraft_pos[1])
    vertical_distance = aircraft_pos[2] - user_pos[2]
    angle_radians = np.arctan2(vertical_distance, horizontal_distance)
    return rad_to_deg(angle_radians)

# Function to predict the future position of the aircraft
def predict_future_position(lat, lon, altitude, groundspeed, track, minutes):
    # Convert groundspeed from knots to feet per minute
    speed_fpm = groundspeed * 6076.12 / 60  # 1 nautical mile = 6076.12 feet

    # Calculate the change in position
    distance_traveled = speed_fpm * minutes

    # Calculate new latitude and longitude based on the track angle
    delta_lat = distance_traveled * np.cos(deg_to_rad(track)) / EARTH_RADIUS_FEET
    delta_lon = distance_traveled * np.sin(deg_to_rad(track)) / (EARTH_RADIUS_FEET * np.cos(deg_to_rad(lat)))

    new_lat = lat + rad_to_deg(delta_lat)
    new_lon = lon + rad_to_deg(delta_lon)

    return new_lat, new_lon, altitude

# Function to find the closest point of approach, returns minimum distance in nautical miles
def closest_approach(user_lat, user_lon, user_alt, aircraft_lat, aircraft_lon, aircraft_alt, future_lat, future_lon, future_alt):
    # Sampling points along the aircraft's path to estimate closest approach
    num_samples = 100
    min_distance = float('inf')
    closest_point = None
    t_closest = 0

    for i in range(num_samples + 1):
        t = i / num_samples
        interp_lat = aircraft_lat + t * (future_lat - aircraft_lat)
        interp_lon = aircraft_lon + t * (future_lon - aircraft_lon)
        interp_alt = aircraft_alt + t * (future_alt - aircraft_alt)

        distance = compute_3d_distance(user_lat, user_lon, user_alt, interp_lat, interp_lon, interp_alt)

        if distance < min_distance:
            min_distance = distance
            closest_point = (interp_lat, interp_lon, interp_alt)
            t_closest = t

    return closest_point, t_closest, min_distance / 6076.12
