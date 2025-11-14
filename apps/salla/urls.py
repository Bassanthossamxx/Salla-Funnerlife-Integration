from django.urls import path
from .views import salla_webhook, list_orders , sync_all_orders
urlpatterns = [
    path("webhook/", salla_webhook),
    path("orders/", list_orders),
    path("orders/sync/", sync_all_orders),

]
