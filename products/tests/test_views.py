import pytest
from django.urls import reverse
from djmoney.money import Money
from rest_framework import status

from products.models import Order
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

    def test_cart_owner_after_login(self, api_client, add_products_to_cart, create_user, constants):
        """
        Test that after a user logs in, the current cart becomes associated with that user
        and the total amount is as expected.
        """

        # Step 1: Get the current Cart (before authentication) and check that it has no user
        current_cart_url = reverse("products:cart-current")
        response = api_client.get(current_cart_url)
        assert response.status_code == 200

        cart_data = response.data  # Use response.data for consistency
        cart_id_before_login = cart_data["id"]  # Store the cart ID before login

        cart = Order.objects.get(id=cart_id_before_login)
        assert cart.user is None, "Cart user should be None before login"

        # Step 2: Authenticate with a user
        user = create_user  # Ensure this fixture creates a user with password 'testpassword'
        login_successful = api_client.login(username=user.username, password="testpassword")
        assert login_successful, "Login should be successful"

        # Step 3: Get the current Cart (after authentication) and
        # verify it persists and has the correct user
        response = api_client.get(current_cart_url)
        assert response.status_code == 200

        cart_data = response.data
        cart_id_after_login = cart_data["id"]
        assert cart_id_after_login == cart_id_before_login, "Cart ID should persist after login"

        cart = Order.objects.get(id=cart_id_after_login)
        assert cart.user == user, "Cart should be associated with the logged-in user"

        # Step 4: Verify the total amount is as expected
        cart_total_amount = Money(cart_data["total_amount"], "USD")
        assert (
            cart_total_amount == constants["expected_total_amount"]
        ), "Cart total amount should match the expected amount"

    @pytest.mark.parametrize("payment_method", ["cash_on_delivery", "stripe"])
    def test_cart_checkout(
        self,
        api_client,
        add_products_to_cart,
        create_user,
        constants,
        checkout_data,
        payment_method,
        mock_stripe_factory,
    ):
        """
        Test that a user can successfully checkout the cart using different payment methods,
        and the order status changes to 'processing' with the correct total amount.
        """
        # Step 1: Authenticate the user
        user = create_user
        login_successful = api_client.login(username=user.username, password="testpassword")
        assert login_successful, "Login should be successful"

        # Step 2: Get the current Order and ensure it belongs to the user and is in 'draft' state
        current_cart_url = reverse("products:cart-current")
        response = api_client.get(current_cart_url)
        assert response.status_code == status.HTTP_200_OK
        cart_data = response.data
        cart_id = cart_data["id"]
        cart = Order.objects.get(id=cart_id)
        assert cart.status == "draft", "Cart should be in 'draft' status before checkout"
        assert cart.user == user, "Cart should belong to the authenticated user"

        # Step 3: Make cart_checkout with current payment_method
        test_checkout_data = checkout_data.copy()
        if payment_method == "stripe":
            test_checkout_data["payment"] = {
                "payment_method": "stripe",
                "payment_method_id": "pm_mock_stripe_payment_method_id",
            }
        else:
            test_checkout_data["payment"] = {"payment_method": "cash_on_delivery"}

        # Use the fixture to mock Stripe if needed
        with mock_stripe_factory(payment_method):
            checkout_url = reverse("products:cart-list")
            response = api_client.post(checkout_url, data=test_checkout_data, format="json")
            assert response.status_code == status.HTTP_201_CREATED, "Checkout should be successful"

        # Step 4: Verify that current cart status is set to processing
        # and its total_amount is expected
        cart.refresh_from_db()
        assert cart.status == "processing", "Cart should be in 'processing' status after checkout"
        cart_total_amount = Money(cart.total_amount, "USD")
        assert (
            cart_total_amount == constants["expected_total_amount"]
        ), "Total amount should match expected total amount"
        # Step 4: Verify that address was saved correctly

        assert cart.address is not None, "Address should be associated with the cart"
        for field in test_checkout_data["address"]:
            expected_value = test_checkout_data["address"][field]
            actual_value = getattr(cart.address, field)
            assert actual_value == expected_value, f"Address field '{field}' should match"

        # Step 5: Verify that payment was saved correctly
        assert cart.payment is not None, "Payment should be associated with the cart"
        assert (
            cart.payment.payment_method == payment_method
        ), f"Payment method should be '{payment_method}'"

        if payment_method == "stripe":
            assert cart.payment.status == "succeeded", "Payment status should be 'succeeded'"
            assert (
                cart.payment.external_id == "pi_mocked_intent_id"
            ), "Payment external ID should match the mocked intent ID"

        # Step 6: Get the current Order and
        # Check Order is empty with new id
        response = api_client.get(current_cart_url)
        assert response.status_code == status.HTTP_200_OK
        new_cart_data = response.data
        new_cart_id = new_cart_data["id"]
        assert new_cart_id != cart_id, "New cart should have a different ID after checkout"
        assert new_cart_data["items"] == [], "New cart should be empty after checkout"
        new_cart_total_amount = Money(new_cart_data["total_amount"], "USD")
        assert new_cart_total_amount == Money(
            0, "USD"
        ), "New cart total amount should be zero after checkout"
