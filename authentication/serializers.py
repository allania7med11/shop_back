from dj_rest_auth.registration.serializers import RegisterSerializer as DefaultRegisterSerializer
from dj_rest_auth.serializers import PasswordResetSerializer as DefaultPasswordResetSerializer
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from authentication.forms import AllAuthPasswordResetForm
from authentication.models import UserProfile
from authentication.utils import check_email_exist


class RegisterSerializer(DefaultRegisterSerializer):
    username = None
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)

    def validate_email(self, email):
        if check_email_exist(email):
            raise serializers.ValidationError(
                _("A user is already registered with this e-mail address."),
            )
        return super().validate_email(email)

    def get_cleaned_data(self):
        return {
            "email": self.validated_data.get("email", ""),
            "password1": self.validated_data.get("password1", ""),
            "first_name": self.validated_data.get("first_name", ""),
            "last_name": self.validated_data.get("last_name", ""),
        }


class PasswordResetSerializer(DefaultPasswordResetSerializer):
    password_reset_form_class = AllAuthPasswordResetForm


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    profile_photo = serializers.ImageField(required=False)
    is_admin = serializers.BooleanField(source="user.is_staff", read_only=True)

    class Meta:
        model = UserProfile
        fields = ["first_name", "last_name", "email", "profile_photo", "is_admin"]

    def update(self, instance: UserProfile, validated_data):
        user_data = validated_data.pop("user", {})

        instance.user.first_name = user_data.get("first_name", instance.user.first_name)
        instance.user.last_name = user_data.get("last_name", instance.user.last_name)

        if "profile_photo" in validated_data:
            instance.profile_photo = validated_data["profile_photo"]

        instance.user.save()
        instance.save()
        return instance
