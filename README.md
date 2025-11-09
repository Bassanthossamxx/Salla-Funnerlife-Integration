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

## Next Implementation Steps (from SRS Plan)
1. Define data models (players, transactions, api_audit_logs, webhook_events, etc.)
2. Implement Salla webhook ingestion with HMAC verification & idempotency.
3. FunnerLife API client + audit logging.
4. Admin dashboard endpoints & basic UI scaffolding.
5. Manual adjustment endpoint.
6. Health & CSV export utilities.





## Reference
Full specification & acceptance criteria: `docs/SRS.md`.
