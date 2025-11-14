from django.urls import path
from . import views

urlpatterns = [
    path("services/", views.get_services, name="funnerlife-services"),
    path("callback/", funnerlife_callback, name="funnerlife-callback"),
]
