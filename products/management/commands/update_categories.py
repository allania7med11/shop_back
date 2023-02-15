from django.core.management.base import BaseCommand

from products.models import Category, Product


class Command(BaseCommand):
    help = "Command to join smartphones to mobiles category and delete tvs category"

    def handle(self, *args, **options):
        mobiles = Category.objects.filter(slug="mobiles").first()
        Product.objects.filter(category__slug="smartphones").update(category=mobiles)
        smartphones = Category.objects.filter(slug="smartphones").first()
        if smartphones:
            smartphones.delete()
        tvs = Category.objects.filter(slug="tvs").first()
        if tvs:
            tvs.delete()
        self.stdout.write(
            "Smartphones was joined to mobiles category and tvs was deleted successful"
        )
