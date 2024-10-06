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
router.register(r"cart_items", CartItemsViewSet)
router.register(r"addresses", CartAddressViewSet)
router.register(r"cart", CartViewSet)

urlpatterns = router.urls
