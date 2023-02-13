import json
from rest_framework import serializers
from products.models import Category, Discount, Product, File
from djmoney.money import Money

import cloudinary
import cloudinary.uploader


class ProductMapSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=500)
    category = serializers.CharField(max_length=200)
    images = serializers.ListField(child=serializers.URLField())
    price = serializers.FloatField()
    discountPercentage = serializers.FloatField()

    def validate_title(self, title):
        qs = Product.objects.filter(name=title)
        if len(qs) > 0:
            raise serializers.ValidationError(
                {"title": "Product with this name already exist"}
            )
        return title

    def create(self, validated_data):
        discount = None
        if validated_data["discountPercentage"]:
            discount, created = Discount.objects.get_or_create(
                percent=validated_data["discountPercentage"],
                defaults={"name": f"{validated_data['discountPercentage']} %"},
            )
        category, created = Category.objects.get_or_create(
            slug=validated_data["category"],
            defaults={"name": f"{validated_data['category'].capitalize()}"},
        )
        product = Product(
            name=validated_data["title"],
            description=json.dumps(
                {"delta": "", "html": validated_data["description"]}
            ),
            price=Money(validated_data["price"], "USD"),
            discount=discount,
            category=category,
        )
        product.save()
        for img_url in validated_data["images"]:
            response = cloudinary.uploader.upload(img_url)
            public_id = response["public_id"]
            File.objects.create(file=public_id, product=product)
        return product
