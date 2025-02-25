from django.db import transaction

from authentication.models import GuestUser
from chat.models import Chat, Message


def is_message_owner(request, created_by):
    """Checks if the given message belongs to the request user, including guest users."""
    if not request or not request.user:
        return False

    if created_by == request.user:
        return True

    guest_token = request.session.get("guest_token")
    guest_user = GuestUser.objects.filter(user=created_by, token=guest_token).first()

    return guest_user is not None


def migrate_guest_chat_to_user(guest_user, user):
    """
    Transfers all messages from guest chat to user's chat and
    updates only guest user's messages.
    """
    with transaction.atomic():
        guest_chat = Chat.objects.filter(created_by=guest_user.user).first()
        user_chat = Chat.objects.filter(created_by=user).first()

        if guest_chat:
            if not user_chat:
                # If user has no existing chat, reassign guest chat to them
                guest_chat.created_by = user
                guest_chat.save()
                user_chat = guest_chat
            else:
                # Move all messages from guest_chat to user_chat
                Message.objects.filter(chat=guest_chat).update(chat=user_chat)

                # Update only messages created by the guest user
                Message.objects.filter(chat=user_chat, created_by=guest_user.user).update(
                    created_by=user
                )

                # Delete guest chat after merging messages
                guest_chat.delete()

    return guest_user  # Return for cleanup in handle_guest_migration


def get_current_chat(request):
    """
    Returns the current chat if it exists.
    - If authenticated, returns the user's chat.
    - If unauthenticated and guest user exists, returns their chat.
    - DOES NOT create a guest user or chat.
    """
    user = request.user

    if user.is_authenticated:
        return Chat.objects.filter(created_by=user).first()  # Return user chat or None

    # Check for existing guest user
    guest_token = request.session.get("guest_token")
    if not guest_token:
        return None  # No guest user exists, return None

    guest_user = GuestUser.objects.filter(token=guest_token).first()
    if not guest_user:
        return None  # Guest user not found, return None

    return Chat.objects.filter(
        created_by=guest_user.user
    ).first()  # Return guest chat if exists, otherwise None


def get_or_create_current_chat(request):
    """
    Returns the current chat, creating a guest user/chat only if necessary.
    - If authenticated, returns their chat (or creates one if missing).
    - If unauthenticated, creates a guest user and chat if needed.
    """
    user = request.user

    if user.is_authenticated:
        chat, _ = Chat.objects.get_or_create(created_by=user)
        return chat

    # Handle guest user case
    guest_token = request.session.get("guest_token")
    if not guest_token:
        guest_user = GuestUser.objects.create()  # Create a new guest user
        request.session["guest_token"] = guest_user.token
        request.session.modified = True
    else:
        guest_user, _ = GuestUser.objects.get_or_create(token=guest_token)

    chat, _ = Chat.objects.get_or_create(created_by=guest_user.user)
    return chat
