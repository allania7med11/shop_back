from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MessageViewSet

router = DefaultRouter()
router.register(r"messages", MessageViewSet, basename="message")

urlpatterns = [
    path("chats/", include(router.urls)),
]
