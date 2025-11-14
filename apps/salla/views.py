# salla/views.py

import json
import hmac
import hashlib
import os
from datetime import datetime

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import WebhookEvent, SallaOrder, IntegrationToken
from .client import fetch_order_details_from_salla


ORDER_EVENTS = [
    "order.created",
    "order.updated",
    "order.status.updated",
    "order.payment.updated",
    "invoice.created",
]


@csrf_exempt
def salla_webhook(request):
    # GET: List webhooks
    if request.method == "GET":
        events = WebhookEvent.objects.order_by("-received_at")[:100]
        return JsonResponse({
            "count": events.count(),
            "events": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "signature_valid": e.signature_valid,
                    "received_at": e.received_at.isoformat(),
                }
                for e in events
            ]
        }, status=200)

    # POST: Process webhook
    body = request.body

    # Validate signature
    secret = os.getenv("SALLA_WEBHOOK_SECRET")
    signature = request.headers.get("x-salla-signature")

    valid_signature = False
    if secret and signature:
        computed = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        valid_signature = hmac.compare_digest(signature, computed)
        if not valid_signature:
            return HttpResponse(status=401)

    # Parse JSON
    try:
        payload = json.loads(body or "{}")
    except:
        payload = {}

    event_type = payload.get("event") or "unknown"
    event_id = payload.get("event_id") or f"auto-{timezone.now().timestamp()}"
    data = payload.get("data", {})

    # Save webhook event
    WebhookEvent.objects.create(
        event_id=event_id,
        event_type=event_type,
        payload=payload,
        signature_valid=valid_signature
    )
    # Token event (Easy Mode)
    if event_type == "app.store.authorize":
        expires_unix = data.get("expires")
        expires_at = datetime.fromtimestamp(expires_unix) if expires_unix else None

        IntegrationToken.objects.update_or_create(
            provider="SALLA",
            defaults={
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "expires_at": expires_at,
            }
        )
        return JsonResponse({"token_saved": True})
    # Ignore non-order events
    if event_type not in ORDER_EVENTS:
        return JsonResponse({"ignored": True})

    # Extract order_id
    order_id = (
            data.get("id") or
            data.get("order_id") or
            data.get("checkout_id")
    )

    if not order_id:
        return JsonResponse({"no_order_id": True})

    # Fetch full order details
    full_order = fetch_order_details_from_salla(order_id)
    status_slug = full_order.get("status", {}).get("slug", "")

    SallaOrder.objects.update_or_create(
        order_id=order_id,
        defaults={
            "full_payload": full_order,
            "standard_status": status_slug,
            "last_event": event_type,
        }
    )

    return JsonResponse({"saved": True})


# Dashboard: list saved orders
@api_view(["GET"])
def list_orders(request):
    qs = SallaOrder.objects.order_by("-updated_at")

    return Response({
        "count": qs.count(),
        "orders": [
            {
                "order_id": o.order_id,
                "standard_status": o.standard_status,
                "custom_status": o.custom_status,
                "last_event": o.last_event,
                "updated_at": o.updated_at,
            }
            for o in qs
        ]
    })

# Dashboard: order details
@api_view(["GET"])
def get_order_details(request, order_id):
    """
    Return a single saved order + optionally refreshed details from Salla.
    """
    try:
        order = SallaOrder.objects.get(order_id=order_id)
    except SallaOrder.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    # Optional: Fetch fresh details from Salla (if ?refresh=true)
    refresh = request.GET.get("refresh") == "true"

    if refresh:
        full = fetch_order_details_from_salla(order_id)
        if full:
            order.full_payload = full
            order.standard_status = full.get("status", {}).get("slug", "")
            order.save()

    return Response({
        "order_id": order.order_id,
        "standard_status": order.standard_status,
        "custom_status": order.custom_status,
        "last_event": order.last_event,
        "updated_at": order.updated_at,
        "full_payload": order.full_payload,
    })

