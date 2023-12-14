from core.models import Guest
from rest_framework import serializers



class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = ['guest_id']