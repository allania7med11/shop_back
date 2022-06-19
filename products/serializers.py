from rest_framework import serializers

from products.models import Category, Discount, Product


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ["name", "percent", "active"]


class ProductSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer()

    class Meta:
        model = Product
        fields = ["id", "name", "price", "price_currency", "discount", "category"]


class CategorySerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "products"]
