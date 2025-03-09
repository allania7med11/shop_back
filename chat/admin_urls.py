from rest_framework.routers import DefaultRouter

from chat.views import AdminChatViewSet

router = DefaultRouter()
router.register(r"chats", AdminChatViewSet, basename="admin_chat")

urlpatterns = router.urls
