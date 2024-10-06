import pytest
from django.urls import reverse
from rest_framework import status

from products.tests.factories import ProductFactory


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
