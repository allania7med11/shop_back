from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User



class Command(BaseCommand):
    def handle(self, *args, **options):
        User.all_objects.update(password=make_password("shopadmin"))
        self.stdout.write(
            "------- Pearl users updated to password : shopadmin---------"
        )
