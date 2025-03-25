from django.utils.html import strip_tags
from djmoney.money import Money
from langchain.schema import Document

from products.models import Category, Product


def build_product_documents():
    """
    Converts products from the DB into LangChain Documents.
    These will be used to build a searchable vector index.
    """
    docs = []
    products = Product.objects.select_related("category").filter(category__slug="mobiles")

    for product in products:
        price: Money = product.price
        price_str = f"{price.amount} {price.currency}"  # Clean price
        clean_description = strip_tags(product.description.html)
        content = f"{product.name}\n{clean_description}\nPrice: {price_str}"
        category: Category = product.category
        metadata = {
            "product_slug": product.slug,
            "category": category.slug,
        }
        docs.append(Document(page_content=content, metadata=metadata))

    return docs
