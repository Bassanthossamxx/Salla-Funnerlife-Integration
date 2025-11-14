from django.urls import path
from . import views

urlpatterns = [
    path('webhooks/', views.salla_webhook, name='salla_webhook'),
]
