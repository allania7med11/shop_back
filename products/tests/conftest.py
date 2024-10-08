import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from djmoney.money import Money

from products.tests.factories import DiscountFactory, ProductFactory


@pytest.fixture
def product():
    return ProductFactory()


@pytest.fixture
def products():
    return ProductFactory.create_batch(3)


@pytest.fixture
def constants():
    return {
        "product_1": {
            "name": "product_1",
            "price": Money(50.00, "USD"),
            "discount_percent": 10,  # 10% discount
            "quantity": 2,
            # Directly setting the discounted subtotal
            # item_1_subtotal = (50 - (50 * 10 / 100)) * 2 = 90
            "subtotal": Money(90.00, "USD"),
        },
        "product_2": {
            "name": "product_2",
            "price": Money(20.00, "USD"),
            "discount_percent": 20,  # 20% discount
            "quantity": 3,
            # Directly setting the discounted subtotal
            # item_2_subtotal = (20 - (20 * 20 / 100)) * 3 = 48
            "subtotal": Money(48.00, "USD"),
        },
        # Calculating the expected total amount
        # expected_total_amount = 90 + 48 = 128
        "expected_total_amount": Money(138.00, "USD"),
    }


@pytest.fixture
def address_data():
    return {
        "street": "123 Main St",
        "city": "Anytown",
        "zip_code": "12345",
        "country": "USA",
        "phone": "555-1234",
    }


@pytest.fixture
def checkout_data(address_data):
    return {"address": address_data, "payment": {"payment_method": "cash_on_delivery"}}


# Updated fixture to create discounts using the new constants structure
@pytest.fixture
def create_discounts(constants):
    discount_1 = DiscountFactory(percent=constants["product_1"]["discount_percent"])
    discount_2 = DiscountFactory(percent=constants["product_2"]["discount_percent"])
    return discount_1, discount_2


# Updated fixture to create products using the new constants structure
@pytest.fixture
def create_products(create_discounts, constants):
    discount_1, discount_2 = create_discounts
    product_1 = ProductFactory(
        name=constants["product_1"]["name"],
        price=constants["product_1"]["price"],
        discount=discount_1,
    )
    product_2 = ProductFactory(
        name=constants["product_2"]["name"],
        price=constants["product_2"]["price"],
        discount=discount_2,
    )
    return product_1, product_2


# Updated fixture to add products to the cart using the new constants structure
@pytest.fixture
def add_products_to_cart(api_client, create_products, constants):
    product_1, product_2 = create_products
    cart_items_url = reverse("products:cartitems-list")
    products_to_add = [
        {"product": product_1.id, "quantity": constants["product_1"]["quantity"]},
        {"product": product_2.id, "quantity": constants["product_2"]["quantity"]},
    ]

    for product_data in products_to_add:
        api_client.post(cart_items_url, product_data, format="json")

    return product_1, product_2


@pytest.fixture
def create_user():
    # Create a test user with specific credentials
    return User.objects.create_user(
        username="testuser", email="testuser@example.com", password="testpassword"
    )
