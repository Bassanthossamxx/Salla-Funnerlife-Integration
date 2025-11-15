# Salla ↔ FunnerLife Integration Flow

This document explains how the Salla app and the FunnerLife app work together, and what the Salla storefront/frontend needs to send for the integration to succeed.

## 1. High-level Flow

1. **Customer places an order on Salla** in your storefront.
2. **Salla sends a webhook** to your backend (`/salla/webhook/`).
3. The backend **validates the webhook signature** and stores the webhook event.
4. For order events (e.g. `order.created`, `order.status.updated`, etc.), the backend:
   - Fetches full order details from Salla (including line items and options).
   - Saves/updates a `SallaOrder` record in the local database.
5. When the order is in a **paid/processing** state, the backend:
   - For each item, finds the matching `FunnerLifeService` using `sku`.
   - Extracts player information from Salla line item options (Player ID and optional Zone ID).
   - Builds the FunnerLife `target` field and calls the FunnerLife API to create an order.
   - Stores a `FunnerlifeTransaction` record with the FunnerLife response.
6. Later, **FunnerLife calls back** to your backend at `/funnerlife/callback/` to update transaction status.

---

## 2. Salla App (Backend) Responsibilities

### 2.1 Webhook endpoint: `/salla/webhook/`

Implemented in `apps.salla.views.salla_webhook` and exposed via `apps.salla.urls`:

- **URL**: `/salla/webhook/`
- **Methods**:
  - `GET`: returns the last 100 `WebhookEvent` records for debugging/monitoring.
  - `POST`: processes Salla webhooks.

#### 2.1.1 Signature validation

The webhook expects an HMAC SHA256 signature:

- Secret: `SALLA_WEBHOOK_SECRET` (env var).
- Header: `x-salla-signature`.
- Body: the raw request body.

Flow:

1. Read `secret = os.getenv("SALLA_WEBHOOK_SECRET")`.
2. Compute `hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()`.
3. Compare with header `x-salla-signature` using `hmac.compare_digest`.
4. If invalid → return `401` and stop.

#### 2.1.2 Events and payload

Payload shape (simplified):

```json
{
  "event": "order.status.updated",
  "event_id": "...",
  "data": {
    "id": 123456,
    "status": { "slug": "paid" },
    "...": "..."
  }
}
```

The code:

- Stores every webhook as `WebhookEvent` with:
  - `event_id`, `event_type`, `payload`, `signature_valid`.
- For `event == "app.store.authorize"`:
  - Saves/updates an `IntegrationToken` with Salla OAuth tokens.
- For **order-related events** only:

  ```python
  ORDER_EVENTS = [
      "order.created",
      "order.updated",
      "order.status.updated",
      "order.payment.updated",
      "invoice.created",
  ]
  ```

  - It extracts `order_id` from `data.id`, `data.order_id`, or `data.checkout_id`.
  - Calls `fetch_order_details_from_salla(order_id)` to get full order data.

### 2.2 Salla API client

Implemented in `apps.salla.client`.

- Uses an `IntegrationToken` (saved on `app.store.authorize`) to get an access token.
- Refreshes the token if expired (using Salla OAuth `refresh_token`).
- Exposes:
  - `fetch_order_details_from_salla(order_id)` → full order details + items.
  - `fetch_order_items(order_id)` → `items` list.

### 2.3 Local Salla models

Defined in `apps.salla.models`:

- `WebhookEvent`: all received webhooks (for audit/debug).
- `SallaOrder`:
  - `order_id`: Salla order ID.
  - `full_payload`: full JSON data from Salla.
  - `standard_status`: Salla status slug (e.g. `paid`, `processing`).
  - `custom_status`: your own custom status.
  - `last_event`: last webhook event type.
- `IntegrationToken`: Salla OAuth token, refresh token, and expiry.

### 2.4 Helpers for player info

In `apps.salla.services`:

- `extract_player_id(item)`:
  - Reads `item["options"][0]["value"][0]`.
  - Raises exceptions if missing.
- `extract_zone_id(item)`:
  - Reads `item["options"][1]["value"][0]` if present.
  - Returns `None` if there is no zone.
- `build_target(player_id, zone_id, funner_service)`:
  - If `funner_service["category"] == "Mobile Legends"` and `zone_id` is present → returns `"{player_id}|{zone_id}"`.
  - Otherwise returns `player_id`.

> These functions assume that the Salla line item **options** are configured correctly in the storefront (see section 4).

### 2.5 Order listing endpoints

Also in `apps.salla.views`:

- `GET /salla/orders/` → list of saved `SallaOrder` records.
- `GET /salla/orders/<order_id>/` → details of a specific `SallaOrder`, with optional live refresh from Salla using `?refresh=true`.

---

## 3. FunnerLife App (Backend) Responsibilities

### 3.1 Service sync and storage

In `apps.funnerlife.models`:

- `FunnerLifeService`:
  - `service_id`: ID from FunnerLife API.
  - `name`, `category`, `price`, other price tiers, `status`.
- `FunnerlifeTransaction`:
  - `idtrx`: FunnerLife transaction ID.
  - `order`: FK to `salla.SallaOrder`.
  - `sku`: Salla item `sku`.
  - `target`: string sent to FunnerLife (player ID or `player_id|zone_id`).
  - `response`: JSON response from FunnerLife.

In `apps.funnerlife.services`:

- `fetch_and_cache_services(force_refresh=False)`:
  - Calls `FunnerLifeAPIClient.get_services()`.
  - Filters by `ALLOWED_CATEGORIES` (Free Fire, Mobile Legends, etc.).
  - Creates/updates `FunnerLifeService` rows.
  - Deletes services no longer present.
  - Returns a queryset of allowed services.

### 3.2 FunnerLife API client

In `apps.funnerlife.client`:

- `FunnerLifeAPIClient.get_services()`:
  - `POST {BASE_URL}/service` with `api_key`.
  - Returns list of services from FunnerLife.
- `charge_funnerlife(item, funner_service)`:
  - Uses Salla helpers to get `player_id` and `zone_id` from the line item.
  - Uses `build_target(player_id, zone_id, funner_service)` (category-aware).
  - Prepares payload for `https://api.funnerlife.id/order`:

    ```python
    {
      "api_key": settings.FUNNERLIFE_API_KEY,
      "service_id": item["sku"],
      "target": target,
      "kontak": settings.ADMIN_KONTAK,
      "idtrx": <generated uuid>,
      "callback": settings.FUNNERLIFE_CALLBACK_URL,
    }
    ```

  - Sends POST to FunnerLife.
  - Returns dict with `idtrx`, `request_payload`, `response_payload`, `http_status`.

### 3.3 FunnerLife views & URLs

In `apps.funnerlife.views`:

- `GET /funnerlife/services/`:
  - Calls `fetch_and_cache_services()`.
  - Applies filters/sorting using `FunnerLifeServiceFilter`.
  - Returns JSON list of services (id, name, category, prices, status).

- `POST /funnerlife/callback/`:
  - FunnerLife calls this to notify about transaction status.
  - Looks up `FunnerlifeTransaction` by `idtrx`.
  - Attaches callback data to `trx.response["callback"]` and saves.

In `apps.funnerlife.urls`:

```python
urlpatterns = [
    path("services/", views.get_services, name="funnerlife-services"),
    path("callback/", views.funnerlife_callback, name="funnerlife-callback"),
]
```

---

## 4. What the Salla Frontend Must Provide

For the integration to work correctly, the Salla storefront (frontend) must ensure:

### 4.1 Line item `sku` mapping

- Each product in Salla that should trigger a FunnerLife order **must have `sku` equal to the FunnerLife `service_id`**.
  - Example: If FunnerLife service has `id = "ML123"`, then the Salla product SKU should be `"ML123"`.
- This is how the backend finds the right `FunnerLifeService`:

  ```python
  funner_service = FunnerLifeService.objects.get(service_id=sku)
  ```

### 4.2 Custom options for Player ID and Zone ID

The Salla storefront must add product options so the customer can enter their game identifiers.

Expected structure (simplified Salla line item):

```json
{
  "sku": "ML123",
  "options": [
    {
      "name": "Player ID",
      "value": ["123456789"]
    },
    {
      "name": "Zone ID",
      "value": ["9876"]
    }
  ]
}
```

Backend expectations:

- `options[0].value[0]` → **Player ID** (mandatory).
- `options[1].value[0]` → **Zone ID** (optional; only used for Mobile Legends).

If Player ID is missing, the backend raises an exception (`"Missing Player ID option"`).

### 4.3 Order status

The integration only triggers FunnerLife charges when the order status is one of:

```python
["paid", "processing", "under_review"]
```

The Salla platform itself manages these statuses; the frontend just needs to follow normal Salla checkout flow.

### 4.4 Webhook configuration in Salla

In the Salla app settings (developer dashboard):

1. Set the **webhook URL** to your backend endpoint, e.g.
   - Production: `https://your-domain.com/salla/webhook/`
   - Development (via ngrok): `https://<ngrok-id>.ngrok.io/salla/webhook/`
2. Configure the **signing secret** to match `SALLA_WEBHOOK_SECRET` in your backend env.
3. Ensure the app is authorized so `app.store.authorize` is sent and `IntegrationToken` is created.

---

## 5. Environment Variables Needed

The backend expects these settings (usually via env and `settings.py`):

- **Salla**:
  - `SALLA_CLIENT_ID`
  - `SALLA_CLIENT_SECRET`
  - `SALLA_WEBHOOK_SECRET`

- **FunnerLife**:
  - `FUNNERLIFE_API_BASE` (e.g. `https://api.funnerlife.id/`)
  - `FUNNERLIFE_API_KEY`
  - `FUNNERLIFE_CALLBACK_URL` (e.g. `https://your-domain.com/funnerlife/callback/`)
  - `ADMIN_KONTAK` (contact value FunnerLife expects in the `kontak` field)

---

## 6. Summary for Frontend Developers

To integrate your Salla storefront with FunnerLife:

1. **Map products to FunnerLife services** by setting Salla product `sku` = FunnerLife `service_id`.
2. **Configure product options** so the order item includes:
   - `options[0].value[0]` → Player ID (required).
   - `options[1].value[0]` → Zone ID (optional, used for Mobile Legends only).
3. Ensure the Salla app is installed and authorized so that:
   - `app.store.authorize` webhook is sent.
   - The backend stores an `IntegrationToken`.
4. Confirm that Salla webhooks are pointing to `/salla/webhook/` with the correct signing secret.

Once this is done, every paid Salla order for a mapped product will automatically create a corresponding FunnerLife transaction, and the backend will track it via `FunnerlifeTransaction` and callbacks.

