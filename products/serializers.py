from rest_framework import serializers

from products.models import Category, Order, OrderAddress, OrderItems, Product, File, Discount


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

class CartAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderAddress
        fields = ["id", "street", "city", "zip_code", "country", "phone"]


class CartProductSerializer(serializers.HyperlinkedModelSerializer):
    files = FileSerializer(many=True)

    class Meta:
        model = Product
        fields = [
            "slug",
            "id",
            "name",
            "files",
        ]


class CartItemReadSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    class Meta:
        model = OrderItems
        fields = ["id", "product", "quantity", "subtotal"]



class CartSerializer(serializers.ModelSerializer):
    items = CartItemReadSerializer(many=True, read_only=True)
    address = CartAddressSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ["total_amount", "items", "address"]
        read_only_fields = fields