from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app import db
from app.models.user import User, VALID_ROLES
from app.middleware.auth import login_required, admin_required

users_bp = Blueprint("users", __name__)


@users_bp.route("/", methods=["GET"])
@admin_required
def list_users():
    """List all users. Admin only."""
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200


@users_bp.route("/<int:user_id>", methods=["GET"])
@login_required
def get_user(user_id):
    """
    Get a specific user.
    - Admin can view anyone.
    - Others can only view themselves.
    """
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != "admin" and current_user.id != user_id:
        return jsonify({"error": "You can only view your own profile"}), 403

    user = User.query.get_or_404(user_id, description="User not found")
    return jsonify(user.to_dict()), 200


@users_bp.route("/<int:user_id>/role", methods=["PATCH"])
@admin_required
def update_role(user_id):
    """Change a user's role. Admin only."""
    data = request.get_json() or {}
    new_role = data.get("role")

    if new_role not in VALID_ROLES:
        return jsonify({"error": f"role must be one of: {', '.join(VALID_ROLES)}"}), 400

    user = User.query.get_or_404(user_id, description="User not found")
    user.role = new_role
    db.session.commit()
    return jsonify({"message": f"Role updated to '{new_role}'", "user": user.to_dict()}), 200


@users_bp.route("/<int:user_id>/status", methods=["PATCH"])
@admin_required
def update_status(user_id):
    """Activate or deactivate a user. Admin only."""
    data = request.get_json() or {}
    is_active = data.get("is_active")

    if not isinstance(is_active, bool):
        return jsonify({"error": "is_active must be true or false"}), 400

    # Prevent admin from deactivating themselves
    current_user_id = int(get_jwt_identity())
    if user_id == current_user_id and not is_active:
        return jsonify({"error": "You cannot deactivate your own account"}), 400

    user = User.query.get_or_404(user_id, description="User not found")
    user.is_active = is_active
    db.session.commit()
    status = "activated" if is_active else "deactivated"
    return jsonify({"message": f"User {status}", "user": user.to_dict()}), 200


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    """Delete a user. Admin only. Cannot delete yourself."""
    current_user_id = int(get_jwt_identity())
    if user_id == current_user_id:
        return jsonify({"error": "You cannot delete your own account"}), 400

    user = User.query.get_or_404(user_id, description="User not found")
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200
