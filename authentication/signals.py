from django.contrib.auth.signals import user_logged_in
from django.db import transaction
from django.dispatch import receiver

from authentication.models import GuestUser
from authentication.utils import GUEST_TOKEN_COOKIE
from chat.utils import migrate_guest_chat_to_user
from products.utils.orders import migrate_guest_cart_to_user


@receiver(user_logged_in)
def handle_guest_migration(sender, request, user, **kwargs):
    """Convert a guest to a real account on login OR registration.

    Both flows fire ``user_logged_in`` (custom login_view and dj_rest_auth RegisterView via
    allauth), so this single hook covers new and pre-existing accounts. The guest identity
    comes from the ``guest_token`` cookie (session kept as a transition fallback). Cart and
    chat are migrated together in one transaction, then the throwaway guest is deleted and
    the cookie is cleared by GuestCookieMiddleware.
    """
    guest_token = request.COOKIES.get(GUEST_TOKEN_COOKIE) or request.session.get("guest_token")
    if not guest_token:
        return

    guest_user = GuestUser.objects.select_related("user").filter(token=guest_token).first()
    # Nothing to do if the token is stale or somehow already points at this user.
    if not guest_user or guest_user.user_id == user.id:
        return

    with transaction.atomic():
        migrate_guest_cart_to_user(guest_user, user)
        migrate_guest_chat_to_user(guest_user, user)
        # Cart and chat are reassigned, so deleting the guest User won't cascade them away.
        guest_user.user.delete()
        guest_user.delete()

    request.session.pop("guest_token", None)
    request.session.modified = True
    request._clear_guest_cookie = True
