import pytest

from products.tests.factories import ProductFactory


@pytest.fixture
def product():
    return ProductFactory()


@pytest.fixture
def products():
    return ProductFactory.create_batch(3)
