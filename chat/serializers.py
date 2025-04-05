from django.contrib.auth.models import User
from django.templatetags.static import static
from rest_framework import serializers

from authentication.models import GuestUser
from chat.models import Chat, Message
from chat.utils import is_message_owner


class ChatUserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user's first name, last name, and profile photo."""

    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "profile_photo"]

    def get_profile_photo(self, obj):
        """Retrieve profile photo from the related UserProfile model."""
        if hasattr(obj, "profile"):
            if obj.profile.profile_photo:
                return obj.profile.profile_photo.url
            elif obj.profile.is_chatbot:
                return static("chat/img/chatbot_profile.png")  # Uses Django's static file handling
        return None


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for messages including user details."""

    created_by = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "content", "created_by", "created_at", "is_mine"]
        read_only_fields = ["id", "created_by", "created_at", "is_mine"]

    def get_created_by(self, obj):
        """
        If the request exists and the user is authenticated, return the serialized ChatUserProfile.
        Otherwise, check if the message creator is not a GuestUser before returning their details.
        """
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return ChatUserProfileSerializer(obj.created_by).data
        if obj.created_by and not GuestUser.objects.filter(user=obj.created_by).exists():
            return ChatUserProfileSerializer(obj.created_by).data
        return None

    def get_is_mine(self, obj):
        """Check if the message belongs to the request user."""
        request = self.context.get("request")
        return is_message_owner(request, obj.created_by)


class ChatListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing chats, including the creator's details and the latest message.
    """

    created_by = serializers.SerializerMethodField()
    latest_message = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["id", "created_by", "created_at", "latest_message"]
        read_only_fields = ["id", "created_by", "created_at", "latest_message"]

    def get_created_by(self, obj):
        """
        Return the details of the user who created the chat.
        If the creator is a guest user, return None.
        """
        if obj.created_by_id and not GuestUser.objects.filter(user_id=obj.created_by_id).exists():
            return ChatUserProfileSerializer(obj.created_by).data
        return None

    def get_latest_message(self, obj):
        """
        Retrieve the latest message in the chat.
        Returns None if there are no messages.
        """
        latest_msg = obj.messages.order_by("-created_at").first()
        return MessageSerializer(latest_msg).data if latest_msg else None


class ChatDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving a chat, including all messages.
    Supports adding a new message via the `new_message` field.
    """

    created_by = serializers.SerializerMethodField()
    messages = MessageSerializer(many=True)
    new_message = MessageSerializer(write_only=True, required=False)

    class Meta:
        model = Chat
        fields = ["id", "created_by", "created_at", "latest_message", "messages", "new_message"]
        read_only_fields = ["id", "created_by", "created_at", "latest_message", "messages"]

    def get_created_by(self, obj):
        """
        Return the details of the user who created the chat.
        If the creator is a guest user, return None.
        """
        if obj.created_by_id and not GuestUser.objects.filter(user_id=obj.created_by_id).exists():
            return ChatUserProfileSerializer(obj.created_by).data
        return None

    def get_latest_message(self, obj):
        """
        Retrieve the latest message in the chat.
        Returns None if there are no messages.
        """
        latest_msg = obj.messages.order_by("-created_at").first()
        return MessageSerializer(latest_msg).data if latest_msg else None


class ChatMessageAddSerializer(serializers.ModelSerializer):
    """
    Serializer for adding a new message to a chat.
    """

    class Meta:
        model = Message
        fields = ["content"]  # Only allow writing the 'content' field

    def create(self, validated_data):
        """Handles message creation."""
        chat = self.context["chat"]
        user = self.context["request"].user

        new_message = Message.objects.create(
            chat=chat, content=validated_data["content"], created_by=user
        )

        # Update latest message reference in Chat
        chat.latest_message = new_message
        chat.save(update_fields=["latest_message"])

        return new_message
