import json
from django.core.management.base import BaseCommand

from products.management.commands.utils.add_products_from_api.productMap import (
    ProductMapSerializer,
)


class Command(BaseCommand):
    help = "Command to products to database from api"

    def handle(self, *args, **options):
        with open(
            "products/management/commands/utils/add_products_from_api/data.json"
        ) as json_file:
            data = json.load(json_file)
            for productData in data:
                productMap = ProductMapSerializer(data=productData)
                if productMap.is_valid():
                    productMap.save()
