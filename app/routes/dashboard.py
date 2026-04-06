from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func
from datetime import datetime, date
from app import db
from app.models.transaction import Transaction
from app.models.user import User
from app.middleware.auth import analyst_or_admin, login_required

dashboard_bp = Blueprint("dashboard", __name__)


def _base_query(user):
    """Non-deleted transactions. Viewers only see their own."""
    q = Transaction.query.filter_by(is_deleted=False)
    if user.role == "viewer":
        q = q.filter_by(user_id=user.id)
    return q


@dashboard_bp.route("/summary", methods=["GET"])
@login_required
def summary():
    """
    Returns total income, total expenses, and net balance.
    Optional: ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    """
    user = User.query.get(int(get_jwt_identity()))
    q = _base_query(user)
    q = _apply_date_filters(q, request.args)

    rows = q.with_entities(Transaction.type, func.sum(Transaction.amount)).group_by(Transaction.type).all()

    totals = {"income": 0.0, "expense": 0.0}
    for tx_type, total in rows:
        totals[tx_type] = round(total, 2)

    return jsonify({
        "total_income": totals["income"],
        "total_expense": totals["expense"],
        "net_balance": round(totals["income"] - totals["expense"], 2),
    }), 200


@dashboard_bp.route("/by-category", methods=["GET"])
@login_required
def by_category():
    """
    Returns totals grouped by category.
    Optional filters: type, start_date, end_date
    """
    user = User.query.get(int(get_jwt_identity()))
    q = _base_query(user)
    q = _apply_date_filters(q, request.args)

    tx_type = request.args.get("type")
    if tx_type:
        q = q.filter(Transaction.type == tx_type)

    rows = (
        q.with_entities(Transaction.category, Transaction.type, func.sum(Transaction.amount))
        .group_by(Transaction.category, Transaction.type)
        .all()
    )

    result = [{"category": cat, "type": t, "total": round(total, 2)} for cat, t, total in rows]
    return jsonify(result), 200


@dashboard_bp.route("/monthly-trends", methods=["GET"])
@analyst_or_admin
def monthly_trends():
    """
    Monthly income vs expense breakdown.
    Analyst and Admin only.
    Optional: ?year=2024
    """
    user = User.query.get(int(get_jwt_identity()))
    q = _base_query(user)

    year = request.args.get("year", type=int)
    if year:
        q = q.filter(func.strftime("%Y", Transaction.date) == str(year))

    rows = (
        q.with_entities(
            func.strftime("%Y-%m", Transaction.date).label("month"),
            Transaction.type,
            func.sum(Transaction.amount)
        )
        .group_by("month", Transaction.type)
        .order_by("month")
        .all()
    )


    trends = {}
    for month, tx_type, total in rows:
        if month not in trends:
            trends[month] = {"month": month, "income": 0.0, "expense": 0.0}
        trends[month][tx_type] = round(total, 2)

    for month in trends:
        trends[month]["net"] = round(trends[month]["income"] - trends[month]["expense"], 2)

    return jsonify(list(trends.values())), 200


@dashboard_bp.route("/recent", methods=["GET"])
@login_required
def recent_activity():
    """Returns the last N transactions. Default: 10. Max: 50."""
    user = User.query.get(int(get_jwt_identity()))
    limit = min(request.args.get("limit", 10, type=int), 50)

    transactions = (
        _base_query(user)
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(limit)
        .all()
    )

    return jsonify([t.to_dict() for t in transactions]), 200


@dashboard_bp.route("/weekly-trends", methods=["GET"])
@analyst_or_admin
def weekly_trends():
    """
    Weekly income vs expense breakdown.
    Analyst and Admin only.
    """
    user = User.query.get(int(get_jwt_identity()))
    q = _base_query(user)

    rows = (
        q.with_entities(
            func.strftime("%Y-W%W", Transaction.date).label("week"),
            Transaction.type,
            func.sum(Transaction.amount)
        )
        .group_by("week", Transaction.type)
        .order_by("week")
        .all()
    )

    trends = {}
    for week, tx_type, total in rows:
        if week not in trends:
            trends[week] = {"week": week, "income": 0.0, "expense": 0.0}
        trends[week][tx_type] = round(total, 2)

    return jsonify(list(trends.values())), 200




def _apply_date_filters(query, args):
    start_date = args.get("start_date")
    end_date = args.get("end_date")
    if start_date:
        try:
            query = query.filter(Transaction.date >= datetime.strptime(start_date, "%Y-%m-%d").date())
        except ValueError:
            pass
    if end_date:
        try:
            query = query.filter(Transaction.date <= datetime.strptime(end_date, "%Y-%m-%d").date())
        except ValueError:
            pass
    return query
