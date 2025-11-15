from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import fetch_and_cache_services
from .models import FunnerLifeService, FunnerlifeTransaction
from .filters import FunnerLifeServiceFilter
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


@api_view(["GET"])
def get_services(request):
    """Return filtered, sorted FunnerLife services with optional counts."""
    services_qs = fetch_and_cache_services()

    # Apply filters and sorting
    filters = FunnerLifeServiceFilter(services_qs, request.GET)
    filtered_qs = filters.filter_queryset()

    # Optional category counts
    counts = filters.get_category_counts()

    # Prepare response
    data = [
        {
            "id": s.service_id,
            "name": s.name,
            "category": s.category,
            "base_price": float(s.price or 0),
            "gold_price": float(s.price_gold or 0),
            "silver_price": float(s.price_silver or 0),
            "pro_price": float(s.price_pro or 0),
            "status": (
                "active" if (s.status or "").lower() == "aktif"
                else "inactive" if (s.status or "").lower() == "tidak aktif"
                else s.status
            ),
        }
        for s in filtered_qs
    ]

    response = {"count": len(data), "results": data}
    if counts:
        response["category_counts"] = list(counts)

    return Response(response)


@csrf_exempt
def funnerlife_callback(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "invalid json"}, status=400)

    idtrx = data.get("idtrx")
    status_ = data.get("status")
    keterangan = data.get("keterangan", "")

    if not idtrx:
        return JsonResponse({"error": "missing idtrx"}, status=400)

    # Lookup your transaction
    try:
        trx = FunnerlifeTransaction.objects.get(idtrx=idtrx)
    except FunnerlifeTransaction.DoesNotExist:
        return JsonResponse({"error": "transaction not found"}, status=404)

    # Store callback info in response JSON
    trx.response["callback"] = data
    trx.save()

    return JsonResponse({"received": True})
