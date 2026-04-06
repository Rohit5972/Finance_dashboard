from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from datetime import datetime
from app import db
from app.models.transaction import Transaction
from app.models.user import User
from app.middleware.auth import login_required, roles_required
from app.utils.validators import validate_transaction

transactions_bp = Blueprint("transactions", __name__)


def _get_base_query(user):
    """
    Admins and analysts see all transactions.
    Viewers only see their own.
    """
    q = Transaction.query.filter_by(is_deleted=False)
    if user.role == "viewer":
        q = q.filter_by(user_id=user.id)
    return q


@transactions_bp.route("/", methods=["GET"])
@login_required
def list_transactions():
    """
    List transactions with optional filters + pagination.
    Query params: type, category, start_date, end_date, page, per_page
    """
    user = User.query.get(int(get_jwt_identity()))
    q = _get_base_query(user)

    # Filters
    tx_type = request.args.get("type")
    category = request.args.get("category")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if tx_type:
        q = q.filter(Transaction.type == tx_type)
    if category:
        q = q.filter(Transaction.category == category)
    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").date()
            q = q.filter(Transaction.date >= sd)
        except ValueError:
            return jsonify({"error": "start_date must be YYYY-MM-DD"}), 400
    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d").date()
            q = q.filter(Transaction.date <= ed)
        except ValueError:
            return jsonify({"error": "end_date must be YYYY-MM-DD"}), 400

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    paginated = q.order_by(Transaction.date.desc()).paginate(page=page, per_page=per_page)

    return jsonify({
        "data": [t.to_dict() for t in paginated.items],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": paginated.total,
            "pages": paginated.pages,
        }
    }), 200


@transactions_bp.route("/<int:tx_id>", methods=["GET"])
@login_required
def get_transaction(tx_id):
    """Get a single transaction by ID."""
    user = User.query.get(int(get_jwt_identity()))
    tx = Transaction.query.filter_by(id=tx_id, is_deleted=False).first_or_404(description="Transaction not found")

    if user.role == "viewer" and tx.user_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    return jsonify(tx.to_dict()), 200


@transactions_bp.route("/", methods=["POST"])
@roles_required("admin", "analyst")
def create_transaction():
    """Create a new transaction. Analyst and Admin only."""
    data = request.get_json() or {}
    errors, cleaned = validate_transaction(data)

    if errors:
        return jsonify({"errors": errors}), 400

    user_id = int(get_jwt_identity())
    tx = Transaction(user_id=user_id, **cleaned)
    db.session.add(tx)
    db.session.commit()
    return jsonify({"message": "Transaction created", "data": tx.to_dict()}), 201


@transactions_bp.route("/<int:tx_id>", methods=["PATCH"])
@roles_required("admin", "analyst")
def update_transaction(tx_id):
    """Update a transaction. Analyst can only update their own. Admin can update any."""
    user = User.query.get(int(get_jwt_identity()))
    tx = Transaction.query.filter_by(id=tx_id, is_deleted=False).first_or_404(description="Transaction not found")

    if user.role == "analyst" and tx.user_id != user.id:
        return jsonify({"error": "Analysts can only update their own transactions"}), 403

    data = request.get_json() or {}
    errors, cleaned = validate_transaction(data, partial=True)

    if errors:
        return jsonify({"errors": errors}), 400

    for key, value in cleaned.items():
        setattr(tx, key, value)

    db.session.commit()
    return jsonify({"message": "Transaction updated", "data": tx.to_dict()}), 200


@transactions_bp.route("/<int:tx_id>", methods=["DELETE"])
@roles_required("admin")
def delete_transaction(tx_id):
    """Soft delete a transaction. Admin only."""
    tx = Transaction.query.filter_by(id=tx_id, is_deleted=False).first_or_404(description="Transaction not found")
    tx.is_deleted = True
    db.session.commit()
    return jsonify({"message": "Transaction deleted"}), 200
