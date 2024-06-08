from django.urls import path

from authentication.views import SessionView, UserProfileView, get_csrf, login_view, logout_view
from dj_rest_auth.views import PasswordResetView, PasswordResetConfirmView
from dj_rest_auth.registration.views import RegisterView




urlpatterns = [
    path("csrf/", get_csrf, name="csrf"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("session/", SessionView.as_view(), name="session"),
    path("profile/", UserProfileView.as_view(), name="user_profile"),
    path("register/", RegisterView.as_view(), name="register"),
    path("password/reset/", PasswordResetView.as_view(), name="password_reset"),
    path("password/reset/confirm/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]