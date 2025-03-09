from django.urls import include, path

from .views import get_admin_api_schema_view

api_urlpatterns = [
    path("", include(("chat.admin_urls", "admin_chats"), namespace="admin_chats")),
]

schema_view = get_admin_api_schema_view([path("api/admin/", include(api_urlpatterns))])

urlpatterns = [
    path("", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    *api_urlpatterns,
]
