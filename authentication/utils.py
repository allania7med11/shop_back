from django.contrib.auth.models import User


def check_email_exist(email):
    # Check if the email already exists in the User model
    return User.objects.filter(email=email).exists()
