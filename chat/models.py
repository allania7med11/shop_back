from django.contrib.auth.models import User
from django.db import models


class Chat(models.Model):
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    latest_message = models.OneToOneField(
        "Message", null=True, blank=True, on_delete=models.SET_NULL, related_name="latest_in_chat"
    )

    class Meta:
        ordering = ["-latest_message__created_at"]


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    content = models.TextField()
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
