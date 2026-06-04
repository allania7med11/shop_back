from django.core.management.base import BaseCommand

from ai.evals import run


class Command(BaseCommand):
    help = "Run behavioral evals for the AI assistant (calls the real model, costs tokens)."

    def handle(self, *args, **kwargs):
        run()
