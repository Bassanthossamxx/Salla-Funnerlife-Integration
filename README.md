# Salla ↔ FunnerLife Integration

Direct charging workflow: consume Salla `order.paid` webhooks, call FunnerLife charge API, persist transactions + full API audit trail (no wallet/balance tracking). See `docs/SRS.md` for detailed requirements.

## Tech Stack
- Python / Django 5
- Django REST Framework
- SQLite (ledger + audit trail)

## Local Setup (Development)

### 1. Clone & Environment
Create a virtual environment (recommended) and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

(Optional) Create a `.env` file for local overrides:
```
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
APP_VERSION=0.1.0
```

### 2. Apply Migrations
(Initial models are placeholders; schema will evolve per SRS plan.)

```bash
python manage.py migrate
```

### 3. Run Dev Server
```bash
python manage.py runserver
```
Visit: http://127.0.0.1:8000/

## API Docs
- Swagger UI (interactive): `http://localhost:8000/`
- Redoc (reference): `http://localhost:8000/redoc/`
- Raw OpenAPI schema: `http://localhost:8000/schema/` (JSON)

> Authentication is currently disabled for docs (AllowAny); secure in production.

## Project Layout
- `config/` Django project settings & URLs
- `apps/` domain apps: `core`, `dashboard`, `funnerlife`, `salla`, `users`
- `docs/` includes `SRS.md`

## Project Structure (Tree)
```text
Salla-Funnerlife-Integration/
├── manage.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── db.sqlite3
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── __init__.py
├── apps/
│   ├── __init__.py
│   ├── core/
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── tests.py
│   │   └── migrations/
│   │       └── __init__.py
│   ├── dashboard/
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── tests.py
│   │   └── migrations/
│   │       └── __init__.py
│   ├── funnerlife/
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── tests.py
│   │   └── migrations/
│   │       └── __init__.py
│   ├── salla/
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── tests.py
│   │   └── migrations/
│   │       └── __init__.py
│   └── users/
│       ├── apps.py
│       ├── admin.py
│       ├── models.py
│       ├── views.py
│       ├── tests.py
│       └── migrations/
│           └── __init__.py
├── docs/
│   ├── SRS.md
│   └── plan.md
└── (.venv/, .idea/, __pycache__/ omitted)
```

## Reference
Full specification & acceptance criteria: `docs/SRS.md`.
