from rest_framework import routers

from .views import (
    CartAddressViewSet,
    CartItemsViewSet,
    CartViewSet,
    CategoryViewSet,
    ProductViewSet,
)

app_name = "products"

router = routers.DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"products", ProductViewSet)
router.register(r"cart_items", CartItemsViewSet, basename="cartitems")
router.register(r"addresses", CartAddressViewSet, basename="cartaddress")
router.register(r"cart", CartViewSet, basename="cart")

urlpatterns = router.urls
