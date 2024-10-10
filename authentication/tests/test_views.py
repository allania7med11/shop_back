import json

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_get_csrf_token(client):
    response = client.get(reverse("csrf"))
    assert response.status_code == 200
    assert json.loads(response.content) == {"detail": "CSRF cookie set"}


@pytest.mark.django_db
def test_login_view_missing_fields(client):
    response = client.post(reverse("login"), json.dumps({}), content_type="application/json")
    assert response.status_code == 400
    assert json.loads(response.content) == {"detail": "Please provide email and password."}


@pytest.mark.django_db
def test_login_view_invalid_credentials(client):
    data = {"email": "nonexistent@example.com", "password": "wrongpassword"}
    response = client.post(reverse("login"), json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    assert json.loads(response.content) == {"detail": "Invalid credentials."}


@pytest.mark.django_db
def test_login_view_success(api_client, create_user):
    data = {"email": create_user.email, "password": "testpassword"}
    response = api_client.post(
        reverse("login"), data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200
    assert json.loads(response.content) == {"detail": "Successfully logged in."}


@pytest.mark.django_db
def test_logout_view_not_logged_in(api_client):
    response = api_client.get(reverse("logout"))
    assert response.status_code == 400
    assert json.loads(response.content) == {"detail": "You're not logged in."}


@pytest.mark.django_db
def test_logout_view_success(api_client, create_user):
    api_client.login(username=create_user.username, password="testpassword")
    response = api_client.get(reverse("logout"))
    assert response.status_code == 200
    assert json.loads(response.content) == {"detail": "Successfully logged out."}


@pytest.mark.django_db
def test_session_view_authenticated(api_client, create_user):
    api_client.login(username=create_user.username, password="testpassword")
    response = api_client.get(reverse("session"))
    assert response.status_code == 200
    assert json.loads(response.content) == {"isAuthenticated": True}


@pytest.mark.django_db
def test_session_view_not_authenticated(api_client):
    response = api_client.get(reverse("session"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_user_profile_view_authenticated(api_client, create_user):
    api_client.login(username=create_user.username, password="testpassword")
    response = api_client.get(reverse("user_profile"))
    assert response.status_code == 200
