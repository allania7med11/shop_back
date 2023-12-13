from django.urls import include, path
from rest_framework import routers
from products.views import CartItemsViewSet, CategoryViewSet, ProductViewSet

router = routers.DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"products", ProductViewSet)
router.register(r"cart_items", CartItemsViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("api.base.urls.auth")),
]
