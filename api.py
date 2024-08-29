from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Notification
from config import Session
from flask_jwt_extended import create_access_token, JWTManager, get_jwt_identity, jwt_required
from db import get_user_by_id
import os

app = Flask(__name__, static_folder='/webapp')
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False # timedelta(hours=1)
jwt = JWTManager(app)

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400


    with Session() as session:
        # Check if the user already exists
        existing_user = session.query(User).filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "User already exists"}), 400

        # Create a new user
        user = User(email=email, password_hash=generate_password_hash(password))
        session.add(user)
        session.commit()
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']

    # Fetch the user from the database
    with Session() as session:
        user = session.query(User).filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):  # Verify password
            access_token = create_access_token(identity=user.id)
            return jsonify({'access_token': access_token})
        else:
            return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/user/preferences', endpoint="user_preferences", methods=['GET', 'POST'])
@jwt_required()  # Ensure the user is logged in
def user_preferences():
    with Session() as session:
        user = get_user_by_id(session, get_jwt_identity())

        if request.method == 'POST':
            data = request.json
            topic = data.get('topic')
            min_distance = data.get('min_distance')
            min_angle = data.get('min_angle')

            user.topic = topic
            user.min_distance = min_distance
            user.min_angle = min_angle

            session.commit()
            return jsonify({"message": "Preferences updated successfully"}), 200
        else:
            # For GET requests, return current user preferences
            return jsonify({
                "topic": user.topic,
                "min_distance": user.min_distance,
                "min_angle": user.min_angle,
            }), 200

@app.route('/api/user/notifications', endpoint="user_notifications", methods=['GET'])
@jwt_required()  # Ensure the user is logged in
def user_notifications():
    with Session() as session:
        user = get_user_by_id(session, get_jwt_identity())

        start = request.args.get('start', 0, type=int)
        limit = request.args.get('limit', 10, type=int)
        notifications_query = session.query(Notification).filter_by(user_id=user.id) \
            .order_by(Notification.timestamp.desc())
        total_count = notifications_query.count()
        notifications = notifications_query.offset(start).limit(limit)

        return jsonify({
            "notifications": [
                {
                    "timestamp": n.timestamp,
                    "aircraft_hex": n.aircraft_hex,
                    "text": n.notification_text
                } for n in notifications
            ],
            "total_count": total_count
        }), 200

# Serve static files for the web app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')
