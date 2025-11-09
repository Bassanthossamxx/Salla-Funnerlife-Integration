# funner-life details :

### accepted games list:
- Free Fire
- Mobile Legends
- PUBG Mobile
- Roblox
- Honor of Kings
- Marvel Rivals
----
## detials :


###  Goal

You’ll fetch all FunnerLife services from `/service`
→ filter them to your **allowed game list**,
→ store them locally in DB for **5–7 days** (cache duration),
→ automatically **re-fetch + refresh** when cache expires,
→ and **delete** any services not found in the latest response.

---

### Plan — Step by Step

#### **Keep Your Allowed Game Categories**

Your whitelist:

```python
FUNNERLIFE_ALLOWED_GAMES = [
    "Free Fire",
    "Mobile Legends",
    "PUBG Mobile",
    "Roblox",
    "Honor of Kings",
    "Marvel Rivals",
]
```

This ensures only the relevant services are stored and used.

---

#### **Cache Strategy Overview**

You’ll store the services in the database as before, but:

* Add a timestamp field `last_synced_at`.
* When any endpoint (dashboard or internal API) asks for FunnerLife services:

    1. Check if the last sync was **more than 5 days ago**.
    2. If yes → re-fetch from FunnerLife `/service`, filter, update DB.
    3. If no → just return what’s already in the DB (cached data).

🧠 Think of it like:

> “Cache my FunnerLife catalog for 5 days, then auto-refresh.”

---

#### **DB Schema Adjustments**

In your `FunnerLifeService` model, include:

```python
last_synced_at = models.DateTimeField(auto_now=True)
```

Optionally, add:

```python
synced_by_cache = models.BooleanField(default=False)
```

(to track whether it was from auto-cache refresh or manual command)

---

#### **Cache Expiry Logic**

In your service logic (not model), you’ll do:

```python
if last_synced_at is None or (timezone.now() - last_synced_at).days >= 5:
    # Cache expired → fetch new data
    fetch_from_funnerlife()
else:
    # Cache valid → use local data
    return FunnerLifeService.objects.filter(...)
```

✅ This keeps things automatic and lightweight — no cron or manual trigger needed.

---

#### **Filtering Logic**

When fetching from FunnerLife `/service`, filter the API response like this:

```python
filtered_services = [
    s for s in response['data']
    if s['kategori'] in FUNNERLIFE_ALLOWED_GAMES
]
```

✅ You only save the games you care about.

---

#### **DB Refresh (Clean Update)**

Before saving new services:

1. Get all current `service_id` values from DB.
2. Get all new `service_id` values from the latest fetch.
3. For each new service:

    * If exists → update.
    * If not → create.
4. For any old service not in the new list → delete.

✅ This ensures your DB always exactly matches the latest valid set from FunnerLife.

---

#### **API Reuse**

You can expose a backend endpoint:

```
GET /api/funnerlife/services/
```

That:

* Returns the cached services
* Triggers auto-refresh if cache expired

✅ Salla and your dashboard will use this to always fetch up-to-date data safely.

---

#### **Example Timeline**

| Day    | Action                      | Result                    |
| ------ | --------------------------- | ------------------------- |
| Day 0  | First fetch                 | All 6 categories saved    |
| Day 3  | Any request → uses cache    | Fast, no external call    |
| Day 6  | Cache expires               | Auto re-fetches & updates |
| Day 7+ | Continues fresh cache cycle | Always up-to-date         |

✅ This means you never depend on manual runs or background workers.

---

#### **Cleanup Strategy (Delete Old)**

After each refresh:

* Compare new service IDs to old ones.
* Delete any not in the new allowed list.

✅ Keeps your DB perfectly clean (no dead records).

---

#### **Error Handling and Fallbacks**

If FunnerLife is down or returns invalid data:

* Log the error
* Do **not** delete existing services (keep last valid cache)
* Retry automatically next time cache expires again

🧠 That’s important: you don’t want to end up with an empty DB if their API fails once.

---

### Summary of This New Plan

| Step | Action                             | Description                         |
| ---- | ---------------------------------- | ----------------------------------- |
| 1    | Store only allowed game categories | Filter out irrelevant data          |
| 2    | Cache services for 5 days          | Avoid daily API hits                |
| 3    | Auto-refresh when expired          | Replace old data automatically      |
| 4    | Delete outdated services           | Keep DB clean                       |
| 5    | Handle API failures gracefully     | Keep last good cache                |
| 6    | Expose `/api/funnerlife/services`  | Let dashboard/Salla use cached data |

---

