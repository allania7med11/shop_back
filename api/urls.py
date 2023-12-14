from django.urls import include, path
from rest_framework import routers
from core.views import GuestCreateView
from products.views import CartItemsViewSet, CategoryViewSet, ProductViewSet

router = routers.DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"products", ProductViewSet)
router.register(r"cart_items", CartItemsViewSet)


urlpatterns = [
    path("create_guest/", GuestCreateView.as_view(), name='create_guest'),
    path("auth/", include("api.base.urls.auth")),
    path("", include(router.urls)),
]
