from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Message


@receiver(post_save, sender=Message)
def update_chat_latest_message(sender, instance: Message, created, **kwargs):
    """Updates chat's latest_message field when a new message is created."""
    if created:
        instance.chat.latest_message = instance
        instance.chat.save(update_fields=["latest_message"])
