from django.core.management.base import BaseCommand

from products.models import Product
from products.utils.slugify import unique_slugify


class Command(BaseCommand):
    help = "Command to add slugs to products with no slugs"

    def handle(self, *args, **options):
        products = Product.objects.all()
        for product in products:
            if not product.slug:
                unique_slugify(product, product.name)
                product.save()
        self.stdout.write("Slugs were added successfully to products with no slugs")
