# products/tests/factories.py

import factory
from django.utils.text import slugify
from djmoney.money import Money
from faker import Faker

from products.models import Category, Discount, Product

fake = Faker()


class DiscountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Discount

    name = factory.Sequence(lambda n: f"Discount {n}")
    percent = factory.Faker(
        "pydecimal", left_digits=2, right_digits=2, positive=True, min_value=5, max_value=50
    )
    active = True


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    price = factory.LazyFunction(
        lambda: Money(fake.pydecimal(left_digits=4, right_digits=2, positive=True), "USD")
    )
    discount = factory.SubFactory(DiscountFactory)
    category = factory.SubFactory(CategoryFactory)
