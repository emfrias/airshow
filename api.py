from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Notification, Filter, Condition, LastLocation
from config import Session
from flask_jwt_extended import create_access_token, JWTManager, get_jwt_identity, jwt_required
from sqlalchemy import desc
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

            user.topic = topic

            session.commit()
            return jsonify({"message": "Preferences updated successfully"}), 200
        else:
            # For GET requests, return current user preferences
            return jsonify({
                "topic": user.topic,
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

@app.route('/api/user/filters', methods=['POST'])
@jwt_required()  # Ensure the user is logged in
def create_filter():
    data = request.json
    filter_name = data.get('filter_name', 'Unnamed Filter')
    conditions = data.get('conditions', [])

    if not conditions:
        return jsonify({"error": "At least one condition is required"}), 400

    with Session() as session:
        user = get_user_by_id(session, get_jwt_identity())

        # Determine the next evaluation order
        next_order = session.query(Filter).filter_by(user_id=user.id).count() + 1

        # Create the filter
        new_filter = Filter(
            user_id=user.id,
            filter_name=filter_name,
            evaluation_order=next_order
        )
        session.add(new_filter)
        session.commit()

        # Create conditions for the filter
        for condition in conditions:
            condition_type = condition['type']
            condition_value = condition['value']
            new_condition = Condition(
                filter_id=new_filter.id,
                condition_type=condition_type,
                condition_value=condition_value
            )
            session.add(new_condition)

        session.commit()

        return jsonify({"filter_id": new_filter.id, "message": "Filter created successfully"}), 201


@app.route('/api/user/filters', methods=['GET'])
@jwt_required()  # Ensure the user is logged in
def get_filters():
    with Session() as session:
        user = get_user_by_id(session, get_jwt_identity())
        filters = session.query(Filter).filter_by(user_id=user.id).order_by(Filter.evaluation_order).all()

        response = []
        for filter in filters:
            conditions = session.query(Condition).filter_by(filter_id=filter.id).all()
            response.append({
                "filter_id": filter.id,
                "filter_name": filter.filter_name,
                "evaluation_order": filter.evaluation_order,
                "conditions": [{"type": cond.condition_type, "value": cond.condition_value} for cond in conditions]
            })

        return jsonify(response), 200


@app.route('/api/user/filters/<int:filter_id>', methods=['PUT'])
@jwt_required()  # Ensure the user is logged in
def update_filter(filter_id):
    data = request.json
    filter_name = data.get('filter_name')
    evaluation_order = data.get('evaluation_order')
    conditions = data.get('conditions', [])

    with Session() as session:
        user = get_user_by_id(session, get_jwt_identity())
        filter_to_update = session.query(Filter).filter_by(id=filter_id, user_id=user.id).first()

        if not filter_to_update:
            return jsonify({"error": "Filter not found"}), 404

        if filter_name:
            filter_to_update.filter_name = filter_name
        if evaluation_order:
            filter_to_update.evaluation_order = evaluation_order

        # Clear existing conditions and add new ones
        session.query(Condition).filter_by(filter_id=filter_to_update.id).delete()
        for condition in conditions:
            new_condition = Condition(
                filter_id=filter_to_update.id,
                condition_type=condition['type'],
                condition_value=condition['value']
            )
            session.add(new_condition)

        session.commit()

        return jsonify({"message": "Filter updated successfully"}), 200


@app.route('/api/user/filters/<int:filter_id>', methods=['DELETE'])
@jwt_required()  # Ensure the user is logged in
def delete_filter(filter_id):
    with Session() as session:
        user = get_user_by_id(session, get_jwt_identity())
        filter_to_delete = session.query(Filter).filter_by(id=filter_id, user_id=user.id).first()

        if not filter_to_delete:
            return jsonify({"error": "Filter not found"}), 404

        # Delete the filter and its conditions
        session.query(Condition).filter_by(filter_id=filter_to_delete.id).delete()
        session.delete(filter_to_delete)
        session.commit()

        return jsonify({"message": "Filter deleted successfully"}), 200

@app.route('/api/user/location', methods=['GET'])
@jwt_required()
def get_user_location():
    user_id = get_jwt_identity()
    with Session() as session:
        location = session.query(LastLocation).filter_by(user_id=user_id).order_by(desc(LastLocation.reported_at)).first()

        if location:
            return jsonify({
                "latitude": location.lat,
                "longitude": location.lon,
                "altitude": location.alt,
                "reported_at": location.reported_at
            }), 200
        else:
            return jsonify({"message": "Location not found"}), 404


# Serve static files for the web app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')
