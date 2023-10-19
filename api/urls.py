from django import views
from django.urls import include, path
from rest_framework import routers

from products.views import CategoryViewSet, OrderAPIView, ProductViewSet

router = routers.DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"products", ProductViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("create_order/", OrderAPIView.as_view(), name='create-order'),
]
