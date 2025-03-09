import uuid

from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    profile_photo = CloudinaryField("file", null=True, blank=True)


def generate_uuid():
    return uuid.uuid4().hex


class GuestUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="guest")
    token = models.CharField(max_length=64, unique=True, default=generate_uuid)
    session_created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # If no associated user is provided, create one using token as username
        if not self.user_id:
            # Ensure token is generated (if not already)
            if not self.token:
                self.token = generate_uuid()
            self.user = User.objects.create(username=self.token)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"GuestUser {self.user.id} - {self.token[:8]}"
