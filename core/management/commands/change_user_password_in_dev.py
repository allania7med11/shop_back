from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        User.objects.all().update(password=make_password("shopadmin"))
        self.stdout.write("------- Pearl users updated to password : shopadmin---------")
