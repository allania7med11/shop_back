# products/tests/factories.py

import factory
from django.utils.text import slugify
from djmoney.money import Money
from factory.django import DjangoModelFactory
from faker import Faker

from products.models import Category, Discount, Order, OrderAddress, OrderItems, Product

fake = Faker()


class DiscountFactory(DjangoModelFactory):
    class Meta:
        model = Discount

    name = factory.Sequence(lambda n: f"Discount {n}")
    percent = factory.Faker(
        "pydecimal", left_digits=2, right_digits=2, positive=True, min_value=5, max_value=50
    )
    active = True


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    price = factory.LazyFunction(
        lambda: Money(fake.pydecimal(left_digits=4, right_digits=2, positive=True), "USD")
    )
    discount = factory.SubFactory(DiscountFactory)
    category = factory.SubFactory(CategoryFactory)


class CartFactory(DjangoModelFactory):
    class Meta:
        model = Order


class CartItemsFactory(DjangoModelFactory):
    class Meta:
        model = OrderItems

    order = factory.SubFactory(CartFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker("random_int", min=1, max=10)


class CartAddressFactory(DjangoModelFactory):
    class Meta:
        model = OrderAddress

    order = factory.SubFactory(CartFactory)
    street = factory.Faker("street_address")
    city = factory.Faker("city")
    zip_code = factory.Faker("postcode")
    country = factory.Faker("country")
    phone = factory.Faker("phone_number")
