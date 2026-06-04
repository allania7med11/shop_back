from django.contrib.auth.models import User

from authentication.models import GuestUser

# httpOnly cookie that carries the guest identity across requests (HTTP) and the
# WebSocket handshake. Single source of truth for "who is this anonymous shopper".
GUEST_TOKEN_COOKIE = "guest_token"


def check_email_exist(email):
    # Check if the email already exists in the User model
    return User.objects.filter(email=email).exists()


def get_or_create_guest(token=None):
    """Return the GuestUser for ``token``, or mint a fresh one.

    Token-first and forgiving: an unknown/expired token never raises — we just create a
    new guest (whose ``save`` also creates the backing ``User``). This is the only place
    a guest is materialized.
    """
    if token:
        guest = GuestUser.objects.filter(token=token).first()
        if guest:
            return guest
    return GuestUser.objects.create()


def resolve_actor(user, guest_token=None):
    """The acting ``User`` for cart/chat — the heart of Option B.

    An authenticated user acts as themselves (no guest needed). Otherwise we resolve (or
    create) the guest ``User`` from the token, so the cart and the chat key on the SAME
    user row instead of diverging (the old ``order_uuid`` vs guest-User bug).

    Returns ``(actor_user, guest_token_or_None)`` — the token is ``None`` for real users,
    and the token to persist in the cookie for guests.
    """
    if user is not None and user.is_authenticated:
        return user, None
    guest = get_or_create_guest(guest_token)
    return guest.user, guest.token


def get_actor(request):
    """HTTP entry point: the acting ``User`` for this request.

    Reads the guest token cookie-first (falling back to the legacy session key during the
    transition) and stashes the token to persist on the request, which the guest-cookie
    middleware writes onto the response. Used by the cart and chat resolvers.
    """
    token = request.COOKIES.get(GUEST_TOKEN_COOKIE) or request.session.get("guest_token")
    actor, guest_token = resolve_actor(getattr(request, "user", None), token)
    request._guest_token = guest_token  # None for real users; middleware persists if set
    return actor


def get_actor_from_scope(scope):
    """WebSocket entry point: same resolution from the Channels handshake.

    Cookies are sent on the WS upgrade, so a guest who opens chat before any HTTP request
    still resolves to the same token — closing the "two tokens" gap.
    """
    cookies = scope.get("cookies", {})
    session = scope.get("session", {}) or {}
    token = cookies.get(GUEST_TOKEN_COOKIE) or session.get("guest_token")
    actor, guest_token = resolve_actor(scope.get("user"), token)
    scope["_guest_token"] = guest_token
    return actor
