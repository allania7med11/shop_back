from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from chat.models import Chat, Message
from chat.serializers import ChatSerializer, MessageSerializer
from chat.utils import get_or_create_chat, get_or_create_guest_user


class MessageViewSet(ListModelMixin, CreateModelMixin, GenericViewSet):
    """Handles message submission and retrieval."""

    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [AllowAny]

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


class AdminChatViewSet(ReadOnlyModelViewSet):
    """Admin API for viewing chats and retrieving messages."""

    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        """Return all chats, including user details."""
        return Chat.objects.all()

    @action(detail=True, methods=["GET"])
    def messages(self, request, pk=None):
        """Retrieve messages for a specific chat."""
        chat = self.get_object()
        messages = Message.objects.filter(chat=chat)
        serializer = MessageSerializer(messages, many=True, context={"request": request})
        return Response(serializer.data)
