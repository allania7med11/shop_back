import json
from django.core.management.base import BaseCommand

from products.management.commands.utils.add_products_from_dummyjson.productMap import (
    ProductMapSerializer,
)


class Command(BaseCommand):
    help = "Command to products to database from dummyjson"

    def handle(self, *args, **options):
        with open(
            "products/management/commands/utils/add_products_from_dummyjson/data.json"
        ) as json_file:
            data = json.load(json_file)
            for productData in data["products"]:
                productMap = ProductMapSerializer(data=productData)
                if productMap.is_valid():
                    print(productMap.validated_data)
                    productMap.save()
