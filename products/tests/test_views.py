import pytest
from django.urls import reverse
from djmoney.money import Money
from rest_framework import status

from products.tests.factories import CategoryFactory, ProductFactory


@pytest.mark.django_db
class TestProductViewSet:

    def test_list_products(self, api_client, products):
        url = reverse("products:product-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(products)
        returned_names = {item["name"] for item in response.data}
        expected_names = {product.name for product in products}
        assert returned_names == expected_names

    def test_retrieve_product(self, api_client, product):
        url = reverse("products:product-detail", kwargs={"slug": product.slug})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == product.id
        assert response.data["name"] == product.name
        assert response.data["slug"] == product.slug
        assert float(response.data["price"]) == float(product.price.amount)

    def test_filter_products_by_name(self, api_client):
        ProductFactory(name="Unique Product")
        ProductFactory.create_batch(2)
        url = reverse("products:product-list") + "?search=Unique"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Unique Product"

    def test_product_not_found(self, api_client):
        url = reverse("products:product-detail", kwargs={"slug": "non-existent-slug"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCategoryViewSet:

    def test_list_categories(self, api_client):
        CategoryFactory.create_batch(3)
        url = reverse("products:category-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_retrieve_category(self, api_client):
        category = CategoryFactory()
        url = reverse("products:category-detail", kwargs={"slug": category.slug})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == category.name


@pytest.mark.django_db
class TestCartViewSet:

    def test_initial_cart_total_is_zero(self, api_client):
        # Fetch the current cart's total
        current_cart_url = reverse("products:cart-current")
        response = api_client.get(current_cart_url)

        # Ensure the response is successful
        assert response.status_code == status.HTTP_200_OK

        # Assert that the initial cart total is zero
        initial_total_amount = Money(response.data["total_amount"], "USD")
        assert initial_total_amount == Money(0, "USD")

    def test_create_products_with_discounts(self, create_products, constants):
        # Unpack created products
        product_1, product_2 = create_products

        # Assert product prices and discounts
        assert product_1.price == constants["product_1"]["price"]
        assert product_1.discount.percent == constants["product_1"]["discount_percent"]
        assert product_2.price == constants["product_2"]["price"]
        assert product_2.discount.percent == constants["product_2"]["discount_percent"]

    def test_add_products_to_cart(self, api_client, create_products, constants):
        # Unpack created products
        product_1, product_2 = create_products
        cart_items_url = reverse("products:cartitems-list")

        # Prepare products to add to the cart using constants
        products_to_add = [
            {"product": product_1.id, "quantity": constants["product_1"]["quantity"]},
            {"product": product_2.id, "quantity": constants["product_2"]["quantity"]},
        ]

        # Add products to the cart and assert each addition is successful
        for idx, product_data in enumerate(products_to_add):
            response = api_client.post(cart_items_url, product_data, format="json")
            assert response.status_code == status.HTTP_201_CREATED

    def test_cart_total_after_adding_products(self, api_client, add_products_to_cart, constants):
        # Fetch the updated cart's total amount
        current_cart_url = reverse("products:cart-current")
        response = api_client.get(current_cart_url)

        # Ensure the response is successful
        assert response.status_code == status.HTTP_200_OK

        # Get the cart items from the response
        cart_items = response.data.get("items", [])

        # Check subtotals for each product
        for item in cart_items:
            product_name = item["product"]["name"]
            subtotal = Money(item["subtotal"], "USD")

            # Use product names to identify the correct item in constants
            if product_name == constants["product_1"]["name"]:
                assert subtotal == constants["product_1"]["subtotal"]
            elif product_name == constants["product_2"]["name"]:
                assert subtotal == constants["product_2"]["subtotal"]

        # Use the predefined expected total amount from constants
        updated_total_amount = Money(response.data["total_amount"], "USD")
        assert updated_total_amount == constants["expected_total_amount"]
