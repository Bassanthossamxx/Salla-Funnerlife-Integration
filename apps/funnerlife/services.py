from django.utils import timezone
from datetime import timedelta
from .models import FunnerLifeService
from .client import FunnerLifeAPIClient
from django.conf import settings


ALLOWED_CATEGORIES = [
    "Free Fire",
    "Mobile Legends",
    "PUBG Mobile",
    "Roblox",
    "Honor of Kings",
    "Marvel Rivals",
]


def fetch_and_cache_services(force_refresh=False):
    """Fetch services from FunnerLife and cache them for 5 days."""

    # Check if data is recent enough
    latest = FunnerLifeService.objects.order_by('-last_synced_at').first()
    if latest and not force_refresh:
        diff = timezone.now() - latest.last_synced_at
        if diff.days < 5:
            print(" Using cached FunnerLife services.")
            return FunnerLifeService.objects.filter(category__in=ALLOWED_CATEGORIES)

    print("Fetching latest FunnerLife services...")
    services_data = FunnerLifeAPIClient.get_services()

    filtered = [s for s in services_data if s["kategori"] in ALLOWED_CATEGORIES]
    current_ids = list(FunnerLifeService.objects.values_list("service_id", flat=True))
    new_ids = [s["id"] for s in filtered]

    # Create or update
    for s in filtered:
        FunnerLifeService.objects.update_or_create(
            service_id=s["id"],
            defaults={
                "name": s["nama_layanan"],
                "category": s["kategori"],
                "price": s["harga"],
                "price_gold": s.get("harga_gold"),
                "price_silver": s.get("harga_silver"),
                "price_pro": s.get("harga_pro"),
                "status": s["status"],
                "last_synced_at": timezone.now(),
            }
        )

    # Delete old ones not in the latest set
    FunnerLifeService.objects.exclude(service_id__in=new_ids).delete()

    print(f" Synced {len(filtered)} services.")
    return FunnerLifeService.objects.filter(category__in=ALLOWED_CATEGORIES)

