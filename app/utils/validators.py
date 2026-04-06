from datetime import datetime
from app.models.transaction import VALID_TYPES, VALID_CATEGORIES
from app.models.user import VALID_ROLES


def validate_transaction(data, partial=False):
    """
    Validate transaction input.
    partial=True → only validate fields that are present (for PATCH).
    Returns (errors: list, cleaned: dict).
    """
    errors = []
    cleaned = {}

    if not partial or "amount" in data:
        amount = data.get("amount")
        if amount is None:
            errors.append("amount is required")
        else:
            try:
                amount = float(amount)
                if amount <= 0:
                    errors.append("amount must be greater than 0")
                else:
                    cleaned["amount"] = amount
            except (TypeError, ValueError):
                errors.append("amount must be a number")

    if not partial or "type" in data:
        t = data.get("type")
        if not t:
            errors.append("type is required")
        elif t not in VALID_TYPES:
            errors.append(f"type must be one of: {', '.join(VALID_TYPES)}")
        else:
            cleaned["type"] = t

    if not partial or "category" in data:
        cat = data.get("category")
        if not cat:
            errors.append("category is required")
        elif cat not in VALID_CATEGORIES:
            errors.append(f"category must be one of: {', '.join(VALID_CATEGORIES)}")
        else:
            cleaned["category"] = cat

    if not partial or "date" in data:
        date_str = data.get("date")
        if not date_str:
            errors.append("date is required")
        else:
            try:
                cleaned["date"] = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                errors.append("date must be in YYYY-MM-DD format")

    if "notes" in data:
        notes = data.get("notes", "")
        if notes and len(notes) > 300:
            errors.append("notes cannot exceed 300 characters")
        else:
            cleaned["notes"] = notes

    return errors, cleaned


def validate_user(data, partial=False):
    """Validate user creation / update data."""
    errors = []
    cleaned = {}

    if not partial or "username" in data:
        username = data.get("username", "").strip()
        if not username:
            errors.append("username is required")
        elif len(username) < 3:
            errors.append("username must be at least 3 characters")
        else:
            cleaned["username"] = username

    if not partial or "email" in data:
        email = data.get("email", "").strip().lower()
        if not email:
            errors.append("email is required")
        elif "@" not in email or "." not in email:
            errors.append("email is not valid")
        else:
            cleaned["email"] = email

    if not partial or "password" in data:
        password = data.get("password", "")
        if not password:
            errors.append("password is required")
        elif len(password) < 6:
            errors.append("password must be at least 6 characters")
        else:
            cleaned["password"] = password

    if "role" in data:
        role = data.get("role")
        if role not in VALID_ROLES:
            errors.append(f"role must be one of: {', '.join(VALID_ROLES)}")
        else:
            cleaned["role"] = role

    return errors, cleaned
