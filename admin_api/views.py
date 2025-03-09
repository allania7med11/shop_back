from django.conf import settings
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


def get_admin_api_schema_view(urlpatterns):
    """Generate API schema for admin API documentation."""
    return get_schema_view(
        openapi.Info(
            title="Admin API",
            default_version="v1",
            description="API documentation for admin-only endpoints",
            terms_of_service="https://www.google.com/policies/terms/",
            contact=openapi.Contact(email=settings.DEFAULT_FROM_EMAIL),
            license=openapi.License(name="BSD License"),
        ),
        public=True,
        permission_classes=(permissions.IsAdminUser,),
        patterns=urlpatterns,
        urlconf="admin_api.urls",
    )
