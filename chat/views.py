from rest_framework import permissions, viewsets

from chat.models import Message
from chat.serializers import MessageSerializer
from chat.utils import get_or_create_chat, get_or_create_guest_user


class MessageViewSet(viewsets.ModelViewSet):
    """Handles message submission and retrieval."""

    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Returns messages for the authenticated user or guest user."""
        user = get_or_create_guest_user(self.request)
        chat = get_or_create_chat(user)
        return Message.objects.filter(chat=chat)

    def perform_create(self, serializer):
        """Handles message creation, linking it to the correct chat and user."""
        user = get_or_create_guest_user(self.request)
        chat = get_or_create_chat(user)
        serializer.save(chat=chat, created_by=user)
