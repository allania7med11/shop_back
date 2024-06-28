from rest_framework import routers
from .views import CardAddressViewSet, CartItemsViewSet, CategoryViewSet, ProductViewSet

router = routers.DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"products", ProductViewSet)
router.register(r"cart_items", CartItemsViewSet)
router.register(r"addresses", CardAddressViewSet)

urlpatterns = router.urls
