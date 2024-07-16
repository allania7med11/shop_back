from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from products.models import Category, Order, OrderAddress, OrderItems, Payment, Product, File, Discount
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
            raise serializers.ValidationError({"payment_method_id": "This field is required when payment method is stripe."})
        return data



class CartSerializer(serializers.ModelSerializer):
    items = CartItemReadSerializer(many=True, read_only=True)
    address = CartAddressSerializer(read_only=True)
    payment = PaymentSerializer()
    
    class Meta:
        model = Order
        fields = ["total_amount", "items", "address"]
        read_only_fields = fields
    
    def update(self, instance: Order, validated_data):
        payment_data = validated_data.pop("payment")
        instance.total_amount = validated_data.get("total_amount", instance.total_amount)
        instance.save()
        payment_method = payment_data.get("payment_method")
        email = self.context["request"].user.email
        if payment_method == Payment.STRIPE:
            payment_method_id = payment_data.get("payment_method_id")
            try:
                self.pay_with_stripe(email, instance, payment_method_id)
            except stripe.error.StripeError as e:
                raise serializers.ValidationError({"message": str(e)})
        set_order_to_processing(instance)
    
    def pay_with_stripe(self, email: str, payment_method_id: str, order: Order):
        customer_data = stripe.Customer.list(email=email).data
        if len(customer_data) == 0:
            customer = stripe.Customer.create(
                email=email, payment_method=payment_method_id
            )
        else:
            customer = customer_data[0]
        payment: Payment = order.payment
        intent = stripe.PaymentIntent.create(
            metadata={"order_id": order.id},
            customer=customer.id,
            payment_method=payment_method_id,
            currency="usd",
            amount=order.total_amount,  
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        )
        if intent.status == "succeeded":
            payment.payment_method = "stripe"
            payment.external_id = intent["id"]
            payment.save()
            set_payment_to_succeeded(payment)
        else:
            raise ValidationError("There was an error processing your payment. Please try again with a different payment method.")
    
    def pay_with_cash_on_delivery(self, order: Order):
        pass
