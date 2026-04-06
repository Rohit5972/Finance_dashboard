from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User


def _get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


def login_required(fn):
    """Verify JWT and inject current user. Blocks inactive users."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = _get_current_user()
        if not user or not user.is_active:
            return jsonify({"error": "Account inactive or not found"}), 403
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    """Allow access only to users with one of the specified roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = _get_current_user()
            if not user or not user.is_active:
                return jsonify({"error": "Account inactive or not found"}), 403
            if user.role not in roles:
                return jsonify({
                    "error": f"Access denied. Required role(s): {', '.join(roles)}"
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    return roles_required("admin")(fn)


def analyst_or_admin(fn):
    return roles_required("analyst", "admin")(fn)
