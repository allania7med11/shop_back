from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer as DefaultRegisterSerializer
from django.utils.translation import gettext_lazy as _
from authentication.forms import AllAuthPasswordResetForm
from authentication.utils import check_email_exist
from dj_rest_auth.serializers import PasswordResetSerializer as DefaultPasswordResetSerializer

class RegisterSerializer(DefaultRegisterSerializer):
    username = None
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)


    def validate_email(self, email):
        if check_email_exist(email):
            raise serializers.ValidationError(
                    _('A user is already registered with this e-mail address.'),
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

    
