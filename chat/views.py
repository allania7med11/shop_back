from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from chat.models import Chat, Message
from chat.serializers import (
    ChatDetailSerializer,
    ChatListSerializer,
    ChatMessageAddSerializer,
    MessageSerializer,
)
from chat.utils import get_current_chat, get_or_create_current_chat_by_request


class MessageViewSet(ListModelMixin, CreateModelMixin, GenericViewSet):
    """Handles message submission and retrieval."""

    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Returns messages for the authenticated user or guest user."""
        chat = get_current_chat(self.request)
        return Message.objects.filter(chat=chat) if chat else Message.objects.none()

    def perform_create(self, serializer):
        """Handles message creation, ensuring a chat exists before saving."""
        chat = get_or_create_current_chat_by_request(
            self.request
        )  # Ensures chat exists before message creation
        serializer.save(chat=chat, created_by=chat.created_by)


class AdminChatViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """
    Admin API for managing chats.
    - `list` → Returns all chats (only those with a latest message).
    - `retrieve` → Returns chat details.
    - `add_message` (POST) → Allows adding a new message.
    """

    queryset = Chat.objects.exclude(latest_message__isnull=True)
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == "list":
            return ChatListSerializer
        return ChatDetailSerializer

    @action(detail=True, methods=["post"])
    def add_message(self, request, pk=None):
        chat = self.get_object()
        serializer = ChatMessageAddSerializer(
            data=request.data, context={"chat": chat, "request": request}
        )

        serializer.is_valid(raise_exception=True)
        new_message = serializer.save()

        return Response(MessageSerializer(new_message).data, status=status.HTTP_201_CREATED)
