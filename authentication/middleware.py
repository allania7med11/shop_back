from authentication.utils import GUEST_TOKEN_COOKIE

# Guests should persist for a long time so an abandoned cart survives a browser restart.
GUEST_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year


class GuestCookieMiddleware:
    """Persists the guest identity in an httpOnly cookie.

    ``get_actor`` (called by the cart/chat resolvers) stashes ``request._guest_token`` when
    an anonymous shopper is resolved; this middleware writes it onto the response. It is the
    ONLY place the cookie is set, keeping a single source of truth. After a guest converts
    to a real account, ``handle_guest_migration`` sets ``request._clear_guest_cookie`` and we
    drop the cookie here.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if getattr(request, "_clear_guest_cookie", False):
            response.delete_cookie(GUEST_TOKEN_COOKIE)
            return response

        token = getattr(request, "_guest_token", None)
        if token and request.COOKIES.get(GUEST_TOKEN_COOKIE) != token:
            response.set_cookie(
                GUEST_TOKEN_COOKIE,
                token,
                max_age=GUEST_COOKIE_MAX_AGE,
                httponly=True,
                samesite="Lax",
                # Secure only over HTTPS — otherwise the browser drops it on local http.
                secure=request.is_secure(),
            )
        return response
