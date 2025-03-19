from django.db import transaction

from authentication.models import GuestUser
from chat.models import Chat, Message
from chat.signals import update_latest_message


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
                # Update only messages created by the guest user
                Message.objects.filter(chat=user_chat, created_by=guest_user.user).update(
                    created_by=user
                )
            else:
                # Move all messages from guest_chat to user_chat
                Message.objects.filter(chat=guest_chat).update(chat=user_chat)

                # Update only messages created by the guest user
                Message.objects.filter(chat=user_chat, created_by=guest_user.user).update(
                    created_by=user
                )

                # Manually trigger latest message update for user_chat
                update_latest_message(user_chat)

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


def get_or_create_current_chat(user, guest_token=None):
    """
    Returns the current chat for the given user.
    - If the user is authenticated, fetch or create their chat.
    - If it's a guest user, fetch or create their chat using the guest token.
    """
    if user.is_authenticated:
        chat, _ = Chat.objects.get_or_create(created_by=user)
        return chat

    if guest_token:
        guest_user, _ = GuestUser.objects.get_or_create(token=guest_token)
        chat, _ = Chat.objects.get_or_create(created_by=guest_user.user)
        return chat

    return None  # No valid user or guest token


def get_or_create_current_chat_by_request(request):
    """
    Extracts user and guest_token from Django's HTTP request object
    and calls get_or_create_current_chat.
    """
    user = request.user
    guest_token = request.session.get("guest_token")

    if not guest_token and not user.is_authenticated:
        guest_user = GuestUser.objects.create()
        request.session["guest_token"] = guest_user.token
        request.session.modified = True
        guest_token = guest_user.token

    return get_or_create_current_chat(user, guest_token)


def get_or_create_current_chat_by_scope(scope):
    """
    Extracts user and guest_token from Django Channels WebSocket scope and
    calls get_or_create_current_chat.
    """
    user = scope.get("user", None)
    session = scope.get("session", {})
    guest_token = session.get("guest_token")

    if not guest_token and (not user or not user.is_authenticated):
        guest_user = GuestUser.objects.create()
        scope["session"]["guest_token"] = guest_user.token
        scope["session"].modified = True
        guest_token = guest_user.token

    return get_or_create_current_chat(user, guest_token)
