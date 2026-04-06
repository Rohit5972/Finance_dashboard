# Finance Dashboard Backend

A role-based finance dashboard backend built with **Flask**, **SQLite**, and **JWT authentication**.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | Flask 3.0 |
| Database | SQLite via Flask-SQLAlchemy |
| Auth | JWT (Flask-JWT-Extended) |
| Password hashing | Werkzeug |

---

## Project Structure

```
finance-dashboard/
├── app/
│   ├── __init__.py            # App factory + DB init
│   ├── models/
│   │   ├── user.py            # User model (roles, password hashing)
│   │   └── transaction.py     # Transaction model (soft delete)
│   ├── routes/
│   │   ├── auth.py            # Register, login, /me
│   │   ├── users.py           # User management (admin only)
│   │   ├── transactions.py    # CRUD + filters + pagination
│   │   └── dashboard.py       # Analytics + summary APIs
│   ├── middleware/
│   │   └── auth.py            # JWT + role-based decorators
│   └── utils/
│       └── validators.py      # Input validation
├── config.py
├── run.py
├── requirements.txt
└── README.md
```

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the server
python run.py
```

Server starts at `http://localhost:5000`

A default admin is created automatically on first run:
- **Username:** `admin`
- **Password:** `admin123`

---

## Roles

| Role | Permissions |
|---|---|
| `viewer` | Read own transactions, view own dashboard summary |
| `analyst` | Read all transactions, create/update own, access trends |
| `admin` | Full access — manage users, all transactions, all analytics |

---

## API Reference

All protected routes require:
```
Authorization: Bearer <token>
```

### Auth

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/auth/register` | Public | Register new user (default role: viewer) |
| POST | `/api/auth/login` | Public | Login, receive JWT token |
| GET | `/api/auth/me` | Any logged-in | Get current user profile |

#### Register
```json
POST /api/auth/register
{
  "username": "rohit",
  "email": "rohit@example.com",
  "password": "secret123"
}
```

#### Login
```json
POST /api/auth/login
{
  "username": "admin",
  "password": "admin123"
}
```
Response:
```json
{
  "token": "<jwt>",
  "user": { "id": 1, "username": "admin", "role": "admin", ... }
}
```

---

### Users

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/users/` | Admin | List all users |
| GET | `/api/users/<id>` | Admin or self | Get user by ID |
| PATCH | `/api/users/<id>/role` | Admin | Change user role |
| PATCH | `/api/users/<id>/status` | Admin | Activate/deactivate user |
| DELETE | `/api/users/<id>` | Admin | Delete user |

#### Change Role
```json
PATCH /api/users/2/role
{ "role": "analyst" }
```

#### Change Status
```json
PATCH /api/users/2/status
{ "is_active": false }
```

---

### Transactions

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/transactions/` | All | List transactions (filtered, paginated) |
| GET | `/api/transactions/<id>` | All | Get single transaction |
| POST | `/api/transactions/` | Analyst, Admin | Create transaction |
| PATCH | `/api/transactions/<id>` | Analyst (own), Admin | Update transaction |
| DELETE | `/api/transactions/<id>` | Admin | Soft delete transaction |

#### Create Transaction
```json
POST /api/transactions/
{
  "amount": 5000,
  "type": "income",
  "category": "salary",
  "date": "2024-06-01",
  "notes": "June salary"
}
```

Valid `type` values: `income`, `expense`

Valid `category` values:
- Income: `salary`, `freelance`, `investment`, `gift`
- Expense: `food`, `rent`, `utilities`, `transport`, `entertainment`, `health`, `shopping`, `other`

#### Filter Transactions
```
GET /api/transactions/?type=expense&category=food&start_date=2024-01-01&end_date=2024-06-30&page=1&per_page=20
```

---

### Dashboard

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/dashboard/summary` | All | Total income, expense, net balance |
| GET | `/api/dashboard/by-category` | All | Totals grouped by category |
| GET | `/api/dashboard/recent` | All | Last N transactions (default 10) |
| GET | `/api/dashboard/monthly-trends` | Analyst, Admin | Month-by-month breakdown |
| GET | `/api/dashboard/weekly-trends` | Analyst, Admin | Week-by-week breakdown |

#### Summary Response
```json
{
  "total_income": 50000.0,
  "total_expense": 18500.0,
  "net_balance": 31500.0
}
```

#### Monthly Trends
```
GET /api/dashboard/monthly-trends?year=2024
```
Response:
```json
[
  { "month": "2024-01", "income": 10000.0, "expense": 3500.0, "net": 6500.0 },
  { "month": "2024-02", "income": 10000.0, "expense": 4200.0, "net": 5800.0 }
]
```

---

## Error Handling

All errors return JSON with appropriate HTTP status codes:

| Code | Meaning |
|---|---|
| 400 | Validation error (bad input) |
| 401 | Missing or invalid token |
| 403 | Forbidden (wrong role or inactive account) |
| 404 | Resource not found |
| 409 | Conflict (duplicate username/email) |

Example validation error:
```json
{
  "errors": ["amount must be greater than 0", "date must be in YYYY-MM-DD format"]
}
```

---

## Assumptions & Design Decisions

1. **New users default to `viewer` role** — role upgrades must be done by an admin via `/api/users/<id>/role`
2. **Soft deletes on transactions** — deleted records stay in DB with `is_deleted=True` for audit trail
3. **Analysts see all transactions** but can only modify their own
4. **Viewers see only their own transactions** across all endpoints including dashboard
5. **JWT tokens don't expire** in this dev setup — set `JWT_ACCESS_TOKEN_EXPIRES` in config for production
6. **SQLite is used** for simplicity — can be swapped to PostgreSQL by changing `SQLALCHEMY_DATABASE_URI`

---

## Quick Test Flow

```bash
# 1. Login as admin
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. Use the token (replace TOKEN below)
TOKEN="your_token_here"

# 3. Create a transaction
curl -X POST http://localhost:5000/api/transactions/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":5000,"type":"income","category":"salary","date":"2024-06-01"}'

# 4. Get dashboard summary
curl http://localhost:5000/api/dashboard/summary \
  -H "Authorization: Bearer $TOKEN"
```
