# myapp/management/commands/createsu.py
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from decouple import config

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        User = get_user_model()
        if not User.objects.filter(username=config("DJANGO_SUPERUSER_USERNAME")).exists():
            User.objects.create_superuser(
                username=config("DJANGO_SUPERUSER_USERNAME"),
                email=config("DJANGO_SUPERUSER_EMAIL"),
                password=config("DJANGO_SUPERUSER_PASSWORD"),
                first_name=config("DJANGO_SUPERUSER_FIRSTNAME"),
                last_name=config("DJANGO_SUPERUSER_LASTNAME")
            )
            self.stdout.write(self.style.SUCCESS("Superuser created"))
