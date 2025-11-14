from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .models import WebhookEvent
import hashlib, hmac, json, os


@csrf_exempt
@require_http_methods(["GET", "POST"])
def salla_webhook(request):
    # 🔹 GET → list all events
    if request.method == "GET":
        events = WebhookEvent.objects.all().order_by("-received_at")[:50]
        data = [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "received_at": e.received_at.isoformat(),
                "signature_valid": e.signature_valid,
            }
            for e in events
        ]
        return JsonResponse({"count": len(data), "events": data})

    # 🔹 POST → handle webhook payload
    secret = os.getenv("SALLA_WEBHOOK_SECRET")
    body = request.body
    signature = request.headers.get("x-salla-signature")
    strategy = request.headers.get("x-salla-security-strategy")

    signature_valid = False
    if secret and signature:
        computed_hmac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        signature_valid = hmac.compare_digest(signature, computed_hmac)
        if not signature_valid:
            print("❌ Invalid Salla signature")
            return HttpResponse(status=401)

    try:
        payload = json.loads(body or "{}")
    except json.JSONDecodeError:
        payload = {}

    event_type = payload.get("event", "unknown")
    event_id = (
            payload.get("event_id")
            or payload.get("id")
            or payload.get("data", {}).get("id")
            or f"auto-{timezone.now().timestamp()}"
    )

    WebhookEvent.objects.create(
        event_id=event_id,
        event_type=event_type,
        payload=payload,
        signature_valid=signature_valid,
    )

    print(f"✅ Webhook received: {event_type} | {event_id}")
    return JsonResponse({"status": "received"}, status=200)
