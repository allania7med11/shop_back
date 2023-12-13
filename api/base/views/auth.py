from api.base.serializers.auth import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import (
    TokenObtainPairView
)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer