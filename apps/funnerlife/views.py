from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .services import fetch_and_cache_services
from .models import FunnerLifeService
from .filters import FunnerLifeServiceFilter


@api_view(["GET"])
@permission_classes([AllowAny])
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
            "status": "active" if (s.status or "").lower() == "aktif" else s.status,
        }
        for s in filtered_qs
    ]

    response = {"count": len(data), "results": data}
    if counts:
        response["category_counts"] = list(counts)

    return Response(response)
