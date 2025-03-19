from django.db.models.signals import post_save
from django.db.transaction import on_commit
from django.dispatch import receiver

from chat.models import Chat, Message


@receiver(post_save, sender=Message)
def update_chat_latest_message(sender, instance: Message, created, **kwargs):
    """
    Updates chat's latest_message field whenever a message is created.
    """
    if created:
        update_latest_message(instance.chat)


def update_latest_message(chat):
    """
    Updates the latest_message field in a chat after a message is added, updated, or deleted.
    """
    if not chat:
        return

    latest_message = Message.objects.filter(chat=chat).order_by("-created_at").first()

    def set_latest_message():
        """
        Clears old references before setting a new latest_message.
        """
        if latest_message:
            #  First, remove previous references to prevent IntegrityError
            Chat.objects.filter(latest_message=latest_message).update(latest_message=None)

        #  Now safely update latest_message
        chat.latest_message = latest_message
        chat.save(update_fields=["latest_message"])

    # Ensure this runs only after transaction commits
    on_commit(set_latest_message)
