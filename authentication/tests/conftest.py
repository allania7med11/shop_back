import pytest
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from rest_framework.test import APIClient


@pytest.fixture
def create_user():
    # Create a test user with the credentials
    return User.objects.create_user(
        username="testuser", email="testuser@example.com", password="testpassword"
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def csrf_token(client):
    # Get a CSRF token for the client session
    return get_token(client)
