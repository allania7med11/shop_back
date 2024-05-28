from django.urls import path

from authentication.views import SessionView, UserProfileView,  login_view, logout_view
from dj_rest_auth.registration.views import RegisterView




urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("session/", SessionView.as_view(), name="session"),
    path("profile/", UserProfileView.as_view(), name="user_profile"),
    path("register/", RegisterView.as_view(), name="register"),
]