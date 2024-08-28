from models import User, LastLocation
from flask import request, jsonify
from sqlalchemy.orm import sessionmaker
from api import app
from config import Session

@app.route('/pub', methods=['POST'])
def receive_location():
    user_email = request.headers.get('X-Limit-U')
    data = request.json

    if data['_type'] == 'location':
        lat = data['lat']
        lon = data['lon']
        alt = data['alt'] * 3.28084  # Convert meters to feet

        session = Session()

        # Map email to user ID and update location
        user = session.query(User).filter_by(email=user_email).first()
        if user:
            location = session.query(LastLocation).filter_by(user_id=user.id).first()
            if location:
                location.lat = lat
                location.lon = lon
                location.alt = alt
            else:
                new_location = LastLocation(user_id=user.id, lat=lat, lon=lon, alt=alt)
                session.add(new_location)

            session.commit()

        session.close()
        return jsonify([])

    return '', 204

