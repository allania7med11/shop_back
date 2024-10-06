import pytest
from django.urls import reverse
from djmoney.money import Money
from rest_framework import status

from products.tests.factories import CategoryFactory, DiscountFactory, ProductFactory


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

    def test_create_cart_items_and_check_total(self, api_client):
        # Initialize or fetch the current cart
        current_cart_url = reverse("products:cart-current")
        response = api_client.get(current_cart_url)
        assert response.status_code == status.HTTP_200_OK

        # Get the initial cart's total amount
        initial_total_amount = Money(response.data["total_amount"], "USD")
        assert initial_total_amount == Money(0, "USD")  # Assuming the initial cart is empty

        # Create discounts
        discount_1 = DiscountFactory(percent=10)  # 10% discount
        discount_2 = DiscountFactory(percent=20)  # 20% discount

        # Create products with discounts
        product_1 = ProductFactory(price=Money(50.00, "USD"), discount=discount_1)

        product_2 = ProductFactory(price=Money(20.00, "USD"), discount=discount_2)

        # URL for the CartItemsViewSet
        cart_items_url = reverse("products:cartitems-list")

        # Add the first product to the cart
        response_1 = api_client.post(
            cart_items_url, {"product": product_1.id, "quantity": 2}, format="json"
        )
        assert response_1.status_code == status.HTTP_201_CREATED

        # Add the second product to the cart
        response_2 = api_client.post(
            cart_items_url, {"product": product_2.id, "quantity": 3}, format="json"
        )
        assert response_2.status_code == status.HTTP_201_CREATED

        # Fetch the current cart again to check the updated total amount
        response = api_client.get(current_cart_url)
        assert response.status_code == status.HTTP_200_OK

        # Calculate the expected total amount after applying discounts
        product_1_discounted_price = product_1.price - (product_1.price * discount_1.percent / 100)
        product_2_discounted_price = product_2.price - (product_2.price * discount_2.percent / 100)
        expected_total_amount = (product_1_discounted_price * 2) + (product_2_discounted_price * 3)
        updated_total_amount = Money(response.data["total_amount"], "USD")

        # Verify that the total amount is updated correctly
        assert updated_total_amount == expected_total_amount
