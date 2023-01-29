import json
from django.core.management.base import BaseCommand

from products.management.commands.utils.add_products.productMap import (
    ProductMapSerializer,
)


class Command(BaseCommand):
    help = "Command to add slugs to products with no slugs"

    def handle(self, *args, **options):
        with open(
            "products/management/commands/utils/add_products/data.json"
        ) as json_file:
            data = json.load(json_file)
            productData = data["products"][1]
            productMap = ProductMapSerializer(data=productData)
            if productMap.is_valid():
                print(productMap.validated_data)
                productMap.save()
