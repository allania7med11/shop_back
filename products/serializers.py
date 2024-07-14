from django.conf import settings
from rest_framework import serializers

from products.models import Category, Order, OrderAddress, OrderItems, Payment, Product, File, Discount
import stripe

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
    class Meta:
        model = Payment
        fields = ['external_id', 'payment_method']
    def validate(self, data):
        if data.get('payment_method') == 'stripe' and not data.get('external_id'):
            raise serializers.ValidationError({"external_id": "This field is required when payment method is stripe."})
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
        payment_data = validated_data.pop('payment')
        instance.total_amount = validated_data.get('total_amount', instance.total_amount)
        instance.save()

        payment_method = payment_data.get('payment_method')
        email = self.context['request'].user.email

        try:
            # Checking if customer with provided email already exists
            customer_data = stripe.Customer.list(email=email).data

            # If the array is empty it means the email has not been used yet
            if len(customer_data) == 0:
                # Creating customer
                customer = stripe.Customer.create(
                    email=email, payment_method=payment_method
                )
            else:
                customer = customer_data[0]
            payment = instance.payment

            if payment_method == 'stripe':
                # Create a Stripe PaymentIntent
                intent = stripe.PaymentIntent.create(
                    metadata={'order_id': instance.id},
                    customer=customer.id,
                    payment_method=payment_method,
                    currency='usd',
                    amount=instance.total_amount,  # Stripe expects the amount in cents
                    confirm=True,
                    automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                )
                payment.external_id = intent['id']  # Update the Stripe PaymentIntent ID

            payment.payment_method = payment_method
            payment.save()

            return instance

        except stripe.error.StripeError as e:
            raise serializers.ValidationError({"message": str(e)})