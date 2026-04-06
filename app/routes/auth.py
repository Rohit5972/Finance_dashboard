from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity
from app import db
from app.models.user import User
from app.utils.validators import validate_user
from app.middleware.auth import login_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user. Default role is 'viewer'."""
    data = request.get_json() or {}
    errors, cleaned = validate_user(data)

    if errors:
        return jsonify({"errors": errors}), 400

    if User.query.filter_by(username=cleaned["username"]).first():
        return jsonify({"error": "Username already taken"}), 409
    if User.query.filter_by(email=cleaned["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        username=cleaned["username"],
        email=cleaned["email"],
        role="viewer",  # New users always start as viewer
    )
    user.set_password(cleaned["password"])
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"message": "Registered successfully", "token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login with username + password, receive JWT token."""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is inactive"}), 403

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    """Get the currently authenticated user's profile."""
    from flask_jwt_extended import get_jwt_identity
    user = User.query.get(int(get_jwt_identity()))
    return jsonify(user.to_dict()), 200
