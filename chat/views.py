from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from chat.models import Chat, Message
from chat.serializers import ChatSerializer, MessageSerializer
from chat.utils import get_current_chat, get_or_create_current_chat


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
        chat = get_or_create_current_chat(
            self.request
        )  # Ensures chat exists before message creation
        serializer.save(chat=chat, created_by=chat.created_by)


class AdminChatViewSet(ReadOnlyModelViewSet):
    """Admin API for viewing chats and retrieving messages."""

    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        """Return only chats where latest_message is NOT NULL."""
        return Chat.objects.exclude(latest_message__isnull=True)

    @action(detail=True, methods=["GET", "POST"])
    def messages(self, request, pk=None):
        """Retrieve messages or send a new message to a chat."""
        chat = self.get_object()

        if request.method == "GET":
            # Retrieve messages for the chat
            messages = Message.objects.filter(chat=chat)
            serializer = MessageSerializer(messages, many=True, context={"request": request})
            return Response(serializer.data)

        elif request.method == "POST":
            # Admin sends a new message
            serializer = MessageSerializer(data=request.data, context={"request": request})
            if serializer.is_valid():
                message = serializer.save(chat=chat, created_by=request.user)  # Admin is sender
                return Response(
                    MessageSerializer(message, context={"request": request}).data,
                    status=status.HTTP_201_CREATED,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
