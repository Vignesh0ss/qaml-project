"""
Authentication endpoints: /login and /register.
Uses werkzeug.security for robust password hashing.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.extensions import mongo, bcrypt
from app.schemas import LoginSchema, RegisterSchema
from marshmallow import ValidationError
import re
from werkzeug.security import check_password_hash as werkzeug_check

bp = Blueprint("auth", __name__)


def is_password_strong(password):
    """
    Check if password meets criteria:
    - At least 8 characters
    - At least 1 uppercase
    - At least 1 lowercase
    - At least 1 number
    - At least 1 special character
    """
    if len(password) < 8:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True


@bp.route("/auth/register", methods=["POST"])
def register():
    try:
        data = RegisterSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": err.messages}), 422

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    db = mongo.db
    if db is None:
        return jsonify({"error": "Database not available"}), 503

    try:
        users = db["users"]
        if users.find_one({"$or": [{"username": username}, {"email": email}]}):
            return jsonify({"error": "Username or email already exists"}), 409

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = {
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "role": "researcher", # Default role
            "created_at": None
        }

        from datetime import datetime, timezone
        new_user["created_at"] = datetime.now(timezone.utc).isoformat()

        result = users.insert_one(new_user)
        identity = str(result.inserted_id)
        
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)

        return jsonify({
            "message": "User registered successfully",
            "username": username,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }), 201
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@bp.route("/auth/login", methods=["POST"])
def login():
    try:
        raw_data = request.get_json() or {}
        # Support both email and username as identifiers
        data = LoginSchema().load(raw_data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 422

    identifier = raw_data.get("username") or raw_data.get("email")
    password = data.get("password")

    db = mongo.db
    if db is None:
        return jsonify({"error": "Database offline"}), 503

    users = db["users"]
    try:
        user = users.find_one({"$or": [{"username": identifier}, {"email": identifier}]})
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
            
        stored_hash = user.get("password_hash", "")
        is_legacy = stored_hash.startswith("scrypt:") or stored_hash.startswith("pbkdf2:")
        
        # Verify based on format
        if is_legacy:
            is_valid = werkzeug_check(stored_hash, password)
        else:
            try:
                is_valid = bcrypt.check_password_hash(stored_hash, password)
            except Exception:
                is_valid = False

        if not is_valid:
            return jsonify({"error": "Invalid credentials"}), 401

        # SUCCESSFUL LOGIN -> MIGRATION (if legacy)
        if is_legacy:
            print(f"[Auth] Migrating legacy hash for user: {user.get('username')}")
            new_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            users.update_one({"_id": user["_id"]}, {"$set": {"password_hash": new_hash}})

        identity = str(user["_id"])
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)
    
        return jsonify({
            "message": "User logged in",
            "username": user.get("username"),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }), 200
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@bp.route("/auth/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    email = data.get("email")
    new_password = data.get("new_password")

    if not email or not new_password:
        return jsonify({"error": "Email and new password are required"}), 400

    db = mongo.db
    if db is None:
        return jsonify({"error": "Database offline"}), 503

    users = db["users"]
    try:
        user = users.find_one({"email": email})
        if not user:
            return jsonify({"error": "No account found with this email address"}), 404

        if not is_password_strong(new_password):
            return jsonify({"error": "Password does not meet strength requirements"}), 400

        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        users.update_one({"_id": user["_id"]}, {"$set": {"password_hash": hashed_password}})

        return jsonify({"message": "Password reset successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Password reset failed: {str(e)}"}), 500


@bp.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token}), 200
