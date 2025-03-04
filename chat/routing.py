from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/chats/$", consumers.ChatConsumer.as_asgi()),  # Normal users (auto-detect chat)
    re_path(
        r"ws/admin/chats/(?P<chat_id>\d+)/$", consumers.AdminChatConsumer.as_asgi()
    ),  # Admins (specify chat)
]
