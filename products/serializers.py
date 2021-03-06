from rest_framework import serializers

from products.models import Category, Product, File, Discount


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ["name", "percent", "active"]


class FileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ["url"]

    def get_url(self, obj):
        return obj.get_url()


class ProductSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer()
    files = FileSerializer(many=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "files",
            "price",
            "price_currency",
            "discount",
            "category",
        ]


class CategorySerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "products"]
