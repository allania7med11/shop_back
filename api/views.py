from django.conf import settings
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


def get_api_schema_view(urlpatterns):
    return get_schema_view(
        openapi.Info(
            title="Shoppingify API",
            default_version="v1",
            description="API documentation for Shoppingify",
            terms_of_service="https://www.google.com/policies/terms/",
            contact=openapi.Contact(email=settings.DEFAULT_FROM_EMAIL),
            license=openapi.License(name="BSD License"),
        ),
        public=True,
        permission_classes=(permissions.AllowAny,),
        patterns=urlpatterns,
        urlconf="api.urls",
    )
