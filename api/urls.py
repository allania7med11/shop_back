from django.urls import include, path
from rest_framework import routers
from products.views import CardAddressViewSet, CartItemsViewSet, CategoryViewSet, ProductViewSet

router = routers.DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"products", ProductViewSet)
router.register(r"cart_items", CartItemsViewSet)
router.register(r"addresses", CardAddressViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("authentication.urls")),
]
