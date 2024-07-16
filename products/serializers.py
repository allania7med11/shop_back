from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from products.models import (
    Category,
    Order,
    OrderAddress,
    OrderItems,
    Payment,
    Product,
    File,
    Discount,
)
import stripe

from products.utils.orders import set_order_to_processing, set_payment_to_succeeded

stripe.api_key = settings.STRIPE_SECRET_KEY


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


class PaymentSerializer(serializers.ModelSerializer):
    payment_method_id = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Payment
        fields = ["payment_method", "payment_method_id"]

    def validate(self, data):
        if data.get("payment_method") == "stripe" and not data.get("payment_method_id"):
            raise serializers.ValidationError(
                {
                    "payment_method_id": "This field is required when payment method is stripe."
                }
            )
        return data


class CartSerializer(serializers.ModelSerializer):
    items = CartItemReadSerializer(many=True, read_only=True)
    address = CartAddressSerializer()  
    payment = PaymentSerializer(write_only=True)

    class Meta:
        model = Order
        fields = ["total_amount", "items", "address", "payment"]
        read_only_fields = ["items", "total_amount"]

    def update(self, instance: Order, validated_data):
        instance.set_total_amount()
        address_data = validated_data.get("address")    
        address_serializer = CartAddressSerializer(instance.address, data=address_data)
        if address_serializer.is_valid(raise_exception=True):
            address_serializer.save()
        payment_data = validated_data.pop("payment", None)
        if payment_data:
            self.handle_payment(instance, payment_data)
        instance.total_amount = validated_data.get("total_amount", instance.total_amount)
        instance.save()
        return instance

    def handle_payment(self, instance: Order, payment_data):
        payment_method = payment_data.get("payment_method")
        email = self.context["request"].user.email
        if payment_method == Payment.STRIPE:
            email = self.context["request"].user.email
            payment_method_id = payment_data.get("payment_method_id")
            self.pay_with_stripe(email, instance, payment_method_id)
        set_order_to_processing(instance)


    def pay_with_stripe(self, email, order, payment_method_id):
        try:
            customer_data = stripe.Customer.list(email=email).data
            customer = customer_data[0] if customer_data else stripe.Customer.create(
                email=email, payment_method=payment_method_id
            )
            intent = stripe.PaymentIntent.create(
                customer=customer.id,
                payment_method=payment_method_id,
                amount=order.total_amount,
                currency="usd",
                confirm=True,
                metadata={"order_id": order.id},
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            )
            if intent.status == "succeeded":
                order.payment.update(
                    payment_method="stripe",
                    external_id=intent["id"],
                    status="succeeded"
                )
            else:
                raise serializers.ValidationError("Failed to process payment.")
        except stripe.error.StripeError as e:
            raise serializers.ValidationError({"message": str(e)})

