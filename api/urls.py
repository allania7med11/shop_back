from django.urls import include, path

from .views import get_api_schema_view

api_urlpatterns = [
    path("", include(("products.urls", "products"), namespace="products")),
    path("", include(("chat.urls", "chats"), namespace="chats")),
    path("auth/", include("authentication.urls")),
]

schema_view = get_api_schema_view([path("api/", include(api_urlpatterns))])

urlpatterns = [
    path("", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    *api_urlpatterns,
]
