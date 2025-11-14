# salla/client.py

import os
import requests
from datetime import timedelta
from django.utils import timezone
from .models import IntegrationToken

BASE_URL = "https://api.salla.dev/admin/v2/"
TOKEN_URL = "https://accounts.salla.sa/oauth2/token"

CLIENT_ID = os.getenv("SALLA_CLIENT_ID")
CLIENT_SECRET = os.getenv("SALLA_CLIENT_SECRET")


def refresh_salla_token(token_obj: IntegrationToken):

    if not token_obj.refresh_token:
        raise Exception("No refresh token available for Salla!")

    data = {
        "grant_type": "refresh_token",
        "refresh_token": token_obj.refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    res = requests.post(TOKEN_URL, data=data, timeout=10)
    res.raise_for_status()

    payload = res.json()

    expires_at = None
    if payload.get("expires_in"):
        expires_at = timezone.now() + timedelta(seconds=payload["expires_in"])

    token_obj.access_token = payload["access_token"]
    token_obj.refresh_token = payload.get("refresh_token", token_obj.refresh_token)
    token_obj.expires_at = expires_at
    token_obj.save()

    return token_obj


def get_salla_access_token():
    token = IntegrationToken.objects.filter(provider="SALLA").first()
    if not token:
        raise Exception("Salla token missing. Reinstall the app to receive app.store.authorize.")

    if token.is_expired():
        token = refresh_salla_token(token)

    return token.access_token

def fetch_order_items(order_id):
    access_token = get_salla_access_token()

    url = f"{BASE_URL}orders/items"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        res = requests.get(url, headers=headers, params={"order_id": order_id}, timeout=15)
        if res.status_code == 200:
            return res.json().get("data", []) or []
        else:
            print("Error fetching items:", res.status_code, res.text)
    except Exception as e:
        print("Exception fetching items:", e)

    return []  # always safe fallback

def fetch_order_details_from_salla(order_id):
    access_token = get_salla_access_token()

    url = f"{BASE_URL}orders/{order_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    full = {}

    try:
        res = requests.get(url, headers=headers, timeout=15)

        if res.status_code != 200:
            print("Error fetching order details:", res.status_code, res.text)
            full = {}
        else:
            full = res.json().get("data", {}) or {}

    except Exception as e:
        print("Exception during order fetch:", e)
        full = {}

    # 🔥 ALWAYS fetch item details from correct endpoint
    items = fetch_order_items(order_id)
    full["items"] = items

    return full
