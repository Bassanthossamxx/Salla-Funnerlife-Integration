# Software Requirements Specification (SRS)

**Project:** Salla ↔ FunnerLife — Direct Charging with Full Audit Trail
**Profile:** Player interacts **only with Salla**. **No automated refunds**; Support/Admin handle refunds offline. Internal system keeps a **transaction ledger + API audit trail only** (no wallet/balance tracking).

## Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [Stakeholders & Users](#2-stakeholders--users)
3. [Assumptions & Constraints](#3-assumptions--constraints)
4. [High‑Level Architecture](#4-highlevel-architecture)
5. [Functional Requirements](#5-functional-requirements)
6. [Non‑Functional Requirements](#6-nonfunctional-requirements)
7. [Data Model (Concise, Walletless)](#7-data-model-concise-walletless)
8. [External Interfaces & APIs](#8-external-interfaces--apis)
9. [Key Workflows](#9-key-workflows)
10. [Security & Privacy](#10-security--privacy)
11. [Ops & Observability](#11-ops--observability)
12. [Testing & Acceptance Criteria](#12-testing--acceptance-criteria)
13. [Deployment](#13-deployment)
14. [Risks & Mitigations](#14-risks--mitigations)
15. [Glossary](#15-glossary)
16. [Implementation Plan (Short, in Order)](#16-implementation-plan-short-in-order)

---

## 1. Purpose & Scope

* Deliver near real‑time **direct charging** of FunnerLife when **Salla `order.paid`** fires.
* Provide an internal **Admin dashboard** for visibility, reconciliation, manual **adjustments** (record-only), and webhook replay.
* Use a single source of truth: **transactions + API audit logs** (no internal balances).

**In‑Scope**

* Salla OAuth installation and secure webhook ingestion (`order.paid`).
* FunnerLife **charge** calls with idempotency and correlation IDs.
* Transaction and **API audit** models capturing full request/response payloads.
* Admin dashboard (players, transactions, orders, webhooks, settings).

**Out‑of‑Scope**

* Wallets or internal balance tracking.
* Automated refunds via webhooks.
* Direct player portal/checkout outside Salla.
* Complex background workers (PythonAnywhere free constraint).

---

## 2. Stakeholders & Users

* **Product/Business**: defines packages, pricing, refund policy.
* **Engineering**: implements/operates the integration.
* **Support/Finance**: performs manual adjustments, exports reports.
* **Admin (internal user)**: uses dashboard & runbooks.
* **Player (end user)**: buys only on Salla.

---

## 3. Assumptions & Constraints

* Hosting: **PythonAnywhere Free** (WSGI only, no always‑on workers).
* DB: **SQLite** (acceptable at low/moderate volume; short transactions).
* Outbound internet: PA free **whitelist** only; may require relay or paid plan for FunnerLife host.
* Security: HTTPS; secrets via PA Web tab / `.env`; strict CORS.
* Currency stored per transaction; default **SAR** (extendable).

---

## 4. High‑Level Architecture

```
Player (Salla only) → Salla App (OAuth) → Webhook: order.paid
                                     ↓
                         Our Backend (Django/DRF, SQLite)
                               │
               ┌───────────────┴────────────────┐
               │                                │
       Transactions DB                   API Audit Logs (per call)
               │                                │
               └──────────────▶ FunnerLife API ◀┘
                         (direct charge, no wallet)

Admin Dashboard ↔ Our Backend (adjustments, replay, reporting)
Support (manual refund process) ↔ Admin Dashboard (no auto refund)
```

---

## 4.a Django Apps & Project Setup

The Django backend is organized into the following apps (enabled in `config/settings.py`):
- `apps.core` – base utilities, shared abstractions
- `apps.salla` – Salla OAuth, webhooks, order processing
- `apps.funnerlife` – FunnerLife API client and integration helpers
- `apps.dashboard` – internal admin/dashboard endpoints & views
- `apps.users` – internal user/RBAC scaffolding

Database: SQLite (single file `db.sqlite3`) for ledger + audit trail per constraints in Section 3.

---

## 5. Functional Requirements

**FR‑1** Salla OAuth install: store tokens & webhook secret securely.

**FR‑2** Webhook endpoint `/api/v1/webhooks/salla`: verify HMAC, timestamp tolerance, and **idempotency** by `event_id`.

**FR‑3** On `order.paid`: map `customer_id`→`player_id`; create `PENDING` transaction with `correlation_id`; call FunnerLife **charge**; persist **full request/response**; mark transaction `SUCCESS`/`FAILED`.

**FR‑4** Persist snapshots & logs: `salla_orders`, `webhook_events`, `transactions`, and **`api_audit_logs`** for each external call.

**FR‑5** Admin endpoints/pages: **players**, **transactions** (with FL API details), **orders**, **webhooks** (replay), **integrations** (status), **settings** (RBAC).

**FR‑6** Manual adjustment API/UI (`POST /transactions/adjust`): record-only **ADJUSTMENT** entries (positive or negative) with reason & external_ref; **no internal balance effects**.

**FR‑7** Health & logs: `/health`, searchable logs, CSV export for transactions/audit.

**FR‑8** **No auto refunds**: do **not** subscribe to `order.refunded`; Support handles refunds offline and records an **ADJUSTMENT** entry if needed.

---

## 6. Non‑Functional Requirements

* **Performance**: P95 webhook processing ≤ **5s** (incl. FunnerLife call).
* **Availability**: target **99.9%** (best‑effort on PA free).
* **Observability**: correlation IDs threaded end‑to‑end; charge **success rate**, error distribution, and latency surfaced in dashboard.
* **Security**: OAuth token encryption at rest; HMAC verification; RBAC; audit trail.
* **Scalability**: graceful degradation; scheduled retries (PA scheduled tasks).
* **Compliance**: follow Salla webhook/security guidelines; data minimization.

---

## 7. Data Model (Concise, Walletless)

* **users**: `id, email, password, role{ADMIN,SUPPORT}`
* **players**: `id, salla_customer_id(unique), funnerlife_player_id(unique), mapping_source{AUTO,MANUAL}, first_seen_order_id, created_at, updated_at`
* **transactions**:
  `id, player_id(FK players), type{CHARGE,ADJUSTMENT}, amount, currency, status{PENDING,SUCCESS,FAILED}, external_ref, correlation_id, funnerlife_request_payload(json), funnerlife_response_payload(json), http_status(int), provider_txn_id(text), meta(json), created_at, updated_at`

  * Indexes: `(player_id, created_at desc)`, `(status)`, `(external_ref)`, `(correlation_id unique)`
* **integration_tokens**: `provider{SALLA,FUNNERLIFE}, access/refresh, expires_at, scope, account_id, created_at`
* **salla_orders**: `order_id(unique), player_id(FK), amount, currency, status, raw_payload(json), signature_valid(bool), processed_at`
* **api_audit_logs**:
  `id, provider{FUNNERLIFE,SALLA}, endpoint, method, request_payload(json), response_payload(json), status_code(int), duration_ms(int), correlation_id, transaction_id(FK nullable), created_at`
* **webhook_events**: `provider, event_type, event_id(unique), signature, payload(json), status{RECEIVED,PROCESSED,FAILED}, retry_count, processed_at`
* **audit_logs** (user actions): `actor_id(FK users nullable), action, target_type/id, meta(json), created_at`

> **Removed**: `wallets` table and all wallet references.

---

## 8. External Interfaces & APIs

**Salla**: OAuth app; webhook `order.paid` → `POST /api/v1/webhooks/salla`.
**FunnerLife**: `POST /charges {player_id, amount, currency, correlation_id}` (idempotent).

**Backend REST (examples)**

* Auth: `POST /auth/login`, `POST /auth/refresh`
* Players: `GET /players/:id`, `GET /players?query=` (search & mapping tools)
* Transactions: `GET /transactions?player_id=&status=&from=&to=&q=`, `GET /transactions/:id` (includes FL request/response), `POST /transactions/adjust`
* Audit: `GET /audit?transaction_id=&provider=&from=&to=`
* Integrations: `GET /integrations/salla/status`, `GET /integrations/funnerlife/status`
* Webhooks: `POST /webhooks/salla`, `POST /webhooks/:provider/:id/replay`
* Health/Logs: `GET /health`, `GET /logs`

---

## 9. Key Workflows

**Order Paid (Direct Charge)**

1. Receive webhook → verify HMAC/timestamp → upsert `webhook_events(RECEIVED)`.
2. (Optional) fetch order details; map `salla_customer_id` → `player_id` (auto‑create mapping if first purchase).
3. Create transaction `PENDING` (+ `correlation_id`).
4. Call FunnerLife **charge** (idempotent) and write an **api_audit_logs** row with full request/response.
5. Update transaction `SUCCESS`/`FAILED` with `http_status`, `provider_txn_id`, and store payloads.

**Manual Adjustment (Record‑Only)**

1. Support ticket received.
2. Admin creates **ADJUSTMENT** transaction (positive/negative) with reason & external_ref (no internal balance).
3. If an external refund is processed, record references and documents in `meta`.

**Replay Failed Webhook**

1. Admin opens `/webhooks` → select failed event → **Replay**.
2. Re-runs the same flow with idempotency (`event_id`/`correlation_id`).

---

## 10. Security & Privacy

* Token encryption at rest; short‑lived access + refresh.
* Webhook HMAC verification, timestamp window, event dedupe.
* RBAC: Admin vs Support; least privilege; strict CORS.
* HTTPS only; secrets in env; audit every sensitive action.
* PI data minimization; retention policy for logs & payloads.

---

## 11. Ops & Observability

* Structured JSON logs with `correlation_id`.
* Dashboard tiles: orders today, charge success rate, failed webhooks, median/95th latency.
* Scheduled tasks (PA): retries and daily **reconciliation** (Salla orders vs transactions).
* Backups: regular `db.sqlite3` export; purge/retention for large payloads.

---

## 12. Testing & Acceptance Criteria

**Unit**: Salla/FunnerLife clients (mock HTTP), HMAC verify, idempotency helpers.
**Contract**: sample `order.paid` payloads; signature/timestamp checks; FunnerLife charge contract (codes, errors).
**E2E**: Salla order → webhook → FunnerLife charge → transaction **SUCCESS** with full payloads stored.
**Acceptance** (must have):

* Webhook returns 2xx within SLA; duplicate events don’t double‑charge.
* Dashboard lists transactions with **complete API details**; replay works.
* Adjustments create record‑only entries; audit logs present.
* Health endpoint green; CSV export works.

---

## 13. Deployment

* **Platform**: PythonAnywhere Free (WSGI).
* **DB**: SQLite at `/home/<user>/repo/backend/db.sqlite3`.
* **Static**: `collectstatic` + PA static map.
* **Env**: set via PA Web tab.
* **Outbound**: ensure FunnerLife host reachable (whitelist / relay / paid plan).

---

## 14. Risks & Mitigations

* **PA whitelist blocks FunnerLife** → use relay or upgrade plan.
* **Payload storage growth** → retention windows, compression, offloading.
* **Rate limits / timeouts** → retries with jitter, circuit breakers, idempotency.
* **Token expiry** → refresh & reconnect flows; monitoring.

---

## 15. Glossary

* **Adjustment**: manual, record‑only correction entry (positive/negative).
* **Correlation ID**: UUID threading a single operation across logs/calls.
* **Idempotency**: prevents double‑processing of the same event.

---

## 16. Implementation Plan (Short, in Order)

**DB Schema**

* Drop `wallets` table.
* Alter `transactions`: remove `wallet_id`; add `player_id`, `funnerlife_request_payload`, `funnerlife_response_payload`, `http_status`, `provider_txn_id`, unique `correlation_id`.
* Create `api_audit_logs` table.
* Extend `players` for auto‑mapping fields.

**Backend APIs**

* Remove wallet endpoints; update serializers/views to use `player_id` directly.
* Webhook service: direct FunnerLife **charge** with full audit logging.
* New listing/detail endpoints for transactions and audit logs.

**Frontend Dashboard**

* Remove wallet pages/components and KPIs.
* Update Transactions list/detail to show full FunnerLife API details, `correlation_id`, filters/search.
* Add Audit Logs view & deep-link from transactions.

**Docs & Runbooks**

* Update README/SRS (this doc done).
* Add reconciliation & replay runbooks (ledger-only).
