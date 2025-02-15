from django.contrib.auth.models import User

from authentication.models import GuestUser
from chat.models import Chat


def get_or_create_guest_user(request):
    """Retrieves an existing GuestUser or creates a new one if the user is unauthenticated."""
    if request.user.is_authenticated:
        return request.user  # If logged in, return the authenticated user

    guest_token = request.session.get("guest_token")
    guest_user = GuestUser.objects.filter(token=guest_token).first()

    if not guest_user:
        user = User.objects.create(
            username=f"guest_{User.objects.count() + 1}"
        )  # Generate a unique guest username
        guest_user = GuestUser.objects.create(user=user)
        request.session["guest_token"] = guest_user.token

    return guest_user.user  # Return the associated User instance


def get_or_create_chat(user):
    """Retrieves an existing chat for the user or creates a new one."""
    chat = Chat.objects.filter(created_by=user).first()
    if not chat:
        chat = Chat.objects.create(created_by=user)
    return chat


def is_message_owner(request, created_by):
    """Checks if the given message belongs to the request user, including guest users."""
    if not request or not request.user:
        return False

    if created_by == request.user:
        return True

    guest_token = request.session.get("guest_token")
    guest_user = GuestUser.objects.filter(user=created_by, token=guest_token).first()

    return guest_user is not None
