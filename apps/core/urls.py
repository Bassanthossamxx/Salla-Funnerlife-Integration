from django.urls import path
from .views import AdminLoginView, AdminLogoutView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/login/', AdminLoginView.as_view(), name='admin-login'),
    path('auth/logout/', AdminLogoutView.as_view(), name='admin-logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
