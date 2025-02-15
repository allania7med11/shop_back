from django.contrib.auth.models import User
from rest_framework import serializers

from authentication.models import GuestUser
from chat.models import Chat, Message
from chat.utils import is_message_owner


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user's first name, last name, and profile photo."""

    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["first_name", "last_name", "profile_photo"]

    def get_profile_photo(self, obj):
        """Retrieve profile photo from the related UserProfile model."""
        if hasattr(obj, "profile"):
            return obj.profile.profile_photo.url if obj.profile.profile_photo else None
        return None


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for messages including user details."""

    created_by = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "chat", "content", "created_by", "created_at", "is_mine"]
        read_only_fields = ["id", "chat", "created_by", "created_at", "is_mine"]

    def get_created_by(self, obj):
        """Return user details if they are NOT a GuestUser, otherwise None."""
        if obj.created_by and not GuestUser.objects.filter(user=obj.created_by).exists():
            return UserProfileSerializer(obj.created_by).data
        return None

    def get_is_mine(self, obj):
        """Check if the message belongs to the request user."""
        request = self.context.get("request")
        return is_message_owner(request, obj.created_by)


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ["id", "created_by", "created_at", "latest_message"]
