import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from chat.models import Chat, Message
from chat.serializers import MessageSerializer
from chat.utils import get_or_create_current_chat_by_scope


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        """Handles WebSocket connection and assigns the chat room."""
        self.chat = get_or_create_current_chat_by_scope(self.scope)  # Always returns a valid chat
        if not self.chat:
            self.close()
            return

        self.room_name = f"chat_{self.chat.id}"
        self.room_group_name = self.room_name

        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)

        self.accept()

    def receive(self, text_data):
        """Handles receiving a message via WebSocket."""
        text_data_json = json.loads(text_data)
        content = text_data_json.get("content")

        if not content:
            self.send(text_data=json.dumps({"error": "Message content is required"}))
            return

        # Since GuestUser always has a User, no need for extra checks
        message = Message.objects.create(
            chat=self.chat, created_by=self.chat.created_by, content=content
        )

        # Pass `scope` in context so serializer can correctly determine user/session
        serialized_message = MessageSerializer(message, context={"scope": self.scope}).data

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat_message", "data": serialized_message}
        )

    def chat_message(self, event):
        """Handles broadcasting messages to WebSocket clients."""
        self.send(text_data=json.dumps({"data": event["data"]}))


class AdminChatConsumer(WebsocketConsumer):
    def connect(self):
        """Handles WebSocket connection for admins (only superadmins allowed)."""
        self.user = self.scope["user"]

        # Enforce only superadmins can connect
        if isinstance(self.user, AnonymousUser) or not self.user.is_superuser:
            self.close()
            return

        self.chat_id = self.scope["url_route"]["kwargs"].get("chat_id")
        self.chat = Chat.objects.filter(id=self.chat_id).first()

        if not self.chat:
            self.close()
            return

        self.room_name = f"chat_{self.chat.id}"
        self.room_group_name = self.room_name

        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)

        self.accept()

    def receive(self, text_data):
        """Handles receiving messages via WebSocket."""
        try:
            text_data_json = json.loads(text_data)
            content = text_data_json.get("content")

            if not content:
                self.send(text_data=json.dumps({"error": "Message content is required"}))
                return

            # Ensure only superadmins can send messages
            if not self.user.is_superuser:
                self.send(text_data=json.dumps({"error": "Unauthorized"}))
                return

            message = Message.objects.create(chat=self.chat, created_by=self.user, content=content)

            # Serialize and broadcast the message
            serialized_message = MessageSerializer(message).data
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {"type": "chat_message", "data": serialized_message}
            )

        except json.JSONDecodeError:
            self.send(text_data=json.dumps({"error": "Invalid JSON format"}))
        except Exception:
            self.send(text_data=json.dumps({"error": "An error occurred"}))

    def chat_message(self, event):
        """Handles broadcasting messages to WebSocket clients."""
        self.send(text_data=json.dumps({"data": event["data"]}))
