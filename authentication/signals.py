from django.contrib.auth.signals import user_logged_in
from django.db import transaction
from django.dispatch import receiver

from authentication.models import GuestUser
from chat.utils import migrate_guest_chat_to_user


@receiver(user_logged_in)
def handle_guest_migration(sender, request, user, **kwargs):
    """Handles guest-to-user migration after login."""
    guest_token = request.session.get("guest_token")

    if guest_token:
        with transaction.atomic():
            guest_user = GuestUser.objects.select_related("user").get(token=guest_token)

            # Migrate guest chat messages
            migrate_guest_chat_to_user(guest_user, user)

            # Clean up guest user
            guest_user.user.delete()
            guest_user.delete()

            # Remove guest session
            request.session.pop("guest_token", None)
            request.session.modified = True
