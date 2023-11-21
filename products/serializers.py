from rest_framework import serializers

from products.models import Category, OrderItems, Product, File, Discount


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


class CategoryProductSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="category-detail", lookup_field="slug"
    )

    class Meta:
        model = Category
        fields = ["url", "slug", "id", "name"]


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="product-detail", lookup_field="slug"
    )
    category = CategoryProductSerializer(read_only=True)
    discount = DiscountSerializer()
    current_price = serializers.ReadOnlyField()
    files = FileSerializer(many=True)
    description_html = serializers.SerializerMethodField()

    def get_description_html(self, instance: Product):
        return str(instance.description.html)

    class Meta:
        model = Product
        fields = [
            "url",
            "slug",
            "id",
            "name",
            "files",
            "price",
            "price_currency",
            "discount",
            "current_price",
            "category",
            "description_html",
            "updated_at",
        ]


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="category-detail", lookup_field="slug"
    )
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["url", "slug", "id", "name", "products"]


class CartItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItems
        fields = ["id", "product", "quantity"]
