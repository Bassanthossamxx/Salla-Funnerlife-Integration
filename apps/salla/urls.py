from django.urls import path
from .views import salla_webhook, list_orders , get_order_details
urlpatterns = [
    path("webhook/", salla_webhook),
    path("orders/", list_orders),
    path("orders/<int:order_id>/", get_order_details),
]

