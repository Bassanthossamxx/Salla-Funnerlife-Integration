from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime

class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """JWT login for admin/superuser only."""
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"detail": "Username and password required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not (user.is_superuser or user.is_staff):
            return Response(
                {"detail": "Access denied. Admins only."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Token expiry (in human-readable format)
        exp_timestamp = access_token["exp"]
        exp_time = datetime.fromtimestamp(exp_timestamp).isoformat()

        return Response(
            {
                "refresh": str(refresh),
                "access": str(access_token),
                "access_expires_at": exp_time,
            },
            status=status.HTTP_200_OK,
        )

class AdminLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Logout admin — blacklist refresh token."""
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Logged out successfully."},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
