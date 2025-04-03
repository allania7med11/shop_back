import json
import threading

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from chat.models import Chat, ChatSettings, Message
from chat.serializers import MessageSerializer
from chat.utils import (
    get_ai_response_from_chat,
    get_or_create_chatbot_user,
    get_or_create_current_chat_by_scope,
)


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

    def create_websocket_message(
        self, message_type: str, message: Message, is_typing: bool = None
    ) -> dict:
        """Create a consistent websocket message structure"""
        payload = {"message": MessageSerializer(message).data}
        if is_typing is not None:
            payload["is_typing"] = is_typing

        return {"type": "chat_message", "data": {"message_type": message_type, "payload": payload}}

    def send_typing_status(self, is_typing: bool):
        """Helper function to send typing status."""
        chatbot_user = get_or_create_chatbot_user()
        content = "AI is thinking..." if is_typing else ""
        typing_message = Message(chat=self.chat, created_by=chatbot_user, content=content)

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            self.create_websocket_message("typing", typing_message, is_typing=is_typing),
        )

    def receive(self, text_data):
        """Handles receiving a message via WebSocket."""
        try:
            text_data_json = json.loads(text_data)
            content = text_data_json.get("content")

            if not content:
                self.send(text_data=json.dumps({"error": "Message content is required"}))
                return

            # Create and send client message immediately
            message = Message.objects.create(
                chat=self.chat, created_by=self.chat.created_by, content=content
            )
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, self.create_websocket_message("message", message)
            )

            # Get global AI response setting
            settings = ChatSettings.get_settings()

            # Generate AI response if:
            # 1. Chat owner is staff (includes admins) OR
            # 2. Global AI responses are enabled for regular clients
            if self.chat.created_by.is_staff or settings.ai_for_clients:
                # Send typing status before starting AI response
                self.send_typing_status(is_typing=True)

                # Start AI response generation in a separate thread
                thread = threading.Thread(target=self.handle_ai_response)
                thread.start()

        except json.JSONDecodeError:
            self.send(text_data=json.dumps({"error": "Invalid JSON format"}))
        except Exception as e:
            self.send(text_data=json.dumps({"error": f"An error occurred: {str(e)}"}))

    def handle_ai_response(self):
        """Handle AI response generation in a separate thread."""
        try:
            self.chat.refresh_from_db()

            # Generate and send AI message
            ai_message = get_ai_response_from_chat(self.chat)

            # Stop typing status
            self.send_typing_status(is_typing=False)

            # Send AI response
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, self.create_websocket_message("message", ai_message)
            )
        except Exception as e:
            self.send_typing_status(is_typing=False)  # Stop typing on error
            self.send(text_data=json.dumps({"error": f"AI response error: {str(e)}"}))

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
            serialized_message = MessageSerializer(message, context={"scope": self.scope}).data
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
