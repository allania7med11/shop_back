from django.core.management.base import BaseCommand

from ai.embed import create_vector_index


class Command(BaseCommand):
    help = "Rebuilds the product vector index for AI search"

    def handle(self, *args, **options):
        self.stdout.write("Rebuilding product vector index...")
        create_vector_index()
        self.stdout.write(self.style.SUCCESS("Successfully rebuilt product vector index"))
