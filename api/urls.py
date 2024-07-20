from django.urls import include, path

urlpatterns = [
    path("", include("products.urls")), 
    path("auth/", include("authentication.urls")),
]
