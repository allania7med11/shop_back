import json
from rest_framework import serializers
from products.models import Category, Discount, Product, File
from djmoney.money import Money
import cloudinary
import cloudinary.uploader
from products.serializers import (
    CategoryProductSerializer,
    DiscountSerializer,
    FileSerializer,
)


class FileSerializer(serializers.Serializer):
    url = serializers.URLField()


class ProductMapSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    files = FileSerializer(many=True)
    price = serializers.DecimalField(max_digits=19, decimal_places=4)
    discount = DiscountSerializer(required=False, allow_null=True)
    category = CategoryProductSerializer()
    description_html = serializers.CharField(allow_blank=True)

    def validate_name(self, name):
        qs = Product.objects.filter(name=name)
        if len(qs) > 0:
            raise serializers.ValidationError(
                {"name": "Product with this name already exist"}
            )
        return name

    def create(self, validated_data):
        validated_discount = validated_data["discount"]
        discount = None
        if discount:
            discount, created = Discount.objects.get_or_create(
                percent=validated_discount["percent"],
                defaults={
                    "name": validated_discount["name"],
                    "active": validated_discount["active"],
                },
            )
        validated_category = validated_data["category"]
        category, created = Category.objects.get_or_create(
            name=validated_category["name"],
        )
        product = Product(
            name=validated_data["name"],
            description=json.dumps(
                {"delta": "", "html": validated_data["description_html"]}
            ),
            price=Money(validated_data["price"], "USD"),
            discount=discount,
            category=category,
        )
        product.save()
        for file in validated_data["files"]:
            response = cloudinary.uploader.upload(file["url"])
            public_id = response["public_id"]
            File.objects.create(file=public_id, product=product)
        return product
