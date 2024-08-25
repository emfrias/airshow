CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    topic TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    altitude_feet REAL NOT NULL,
    min_distance REAL NOT NULL,
    min_angle REAL NOT NULL
);

CREATE TABLE last_locations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    lat REAL,
    lon REAL,
    alt_feet REAL
);
