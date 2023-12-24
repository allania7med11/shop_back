from django.urls import path

from api.base.views.auth import SessionView, UserProfileView, get_csrf, login_view, logout_view



urlpatterns = [
    path('csrf/', get_csrf, name='csrf'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('session/', SessionView.as_view(), name='session'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]