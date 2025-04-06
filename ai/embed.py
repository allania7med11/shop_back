import logging
from typing import Dict, Tuple

from django.utils.html import strip_tags
from langchain.schema import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from rest_framework.test import APIRequestFactory

from products.models import Product
from products.serializers import ProductSerializer

# Set up the logger
logger = logging.getLogger(__name__)


def format_product_info(product: Product) -> Tuple[str, Dict]:
    """
    Common function to format product information using the ProductSerializer.
    Returns a tuple of (content, metadata).

    :param product: The product instance to format.
    :return: A tuple containing the formatted content and metadata.
    """
    # If no request is provided, create a mock request
    factory = APIRequestFactory()
    request = factory.get("/")  # Create a mock GET request

    # Serialize the product instance with the request context
    serializer = ProductSerializer(product, context={"request": request})
    product_data = serializer.data

    # Clean the description HTML
    clean_description = strip_tags(product_data["description_html"])

    # Convert current_price to float
    current_price = float(product_data["current_price"])

    # Create the content string
    content = (
        f"{product_data['name']}\n"
        f"Original Price: {product_data['price']} {product_data['price_currency']}\n"
        # Format to 2 decimal places
        f"Discounted Price: {current_price:.2f} {product_data['price_currency']}\n"
    )

    # Include discount information in the content
    discount_info = product_data["discount"]
    if discount_info and discount_info["active"]:
        content += f"Discount: {discount_info['name']} - {discount_info['percent']}%\n"

    content += f"Category: {product_data['category']['name']}\n" f"Description: {clean_description}"

    # Prepare metadata
    metadata = {
        "product_slug": product_data["slug"],
        "category_slug": product_data["category"]["slug"],
        "category_name": product_data["category"]["name"],
        "discount": discount_info,
        "current_price": current_price,
        "price_currency": product_data["price_currency"],
    }

    return content, metadata


def get_product_signature(product: Product) -> str:
    """Create a signature of product data that affects AI responses."""
    factory = APIRequestFactory()
    request = factory.get("/")  # Create a mock GET request

    # Serialize the product instance with the request context
    serializer = ProductSerializer(product, context={"request": request})
    product_data = serializer.data

    # Clean the description HTML for the signature
    clean_description = strip_tags(product_data["description_html"])

    # Convert current_price to float
    current_price = float(product_data["current_price"])

    # Create a unique signature based on relevant fields, including current_price
    return (
        f"{product_data['name']}::{product_data['price']}::{product_data['price_currency']}::"
        f"{clean_description}::{product_data['category']['slug']}::"
        f"{product_data['category']['name']}::{product_data['slug']}::{current_price:.2f}"
    )


def build_product_documents():
    """
    Converts all products from the DB into LangChain Documents.
    These will be used to build a searchable vector index.
    """
    docs = []
    products = Product.objects.select_related("category").all()

    for product in products:
        content, metadata = format_product_info(product)
        docs.append(Document(page_content=content, metadata=metadata))

    return docs


def create_vector_index():
    """
    Builds a FAISS vector index from product documents and saves it locally.
    """
    documents = build_product_documents()

    # Create OpenAI embeddings for semantic similarity
    embeddings = OpenAIEmbeddings()

    # Convert documents into a FAISS vector index
    vectorstore = FAISS.from_documents(documents, embeddings)

    # Save the index to disk (folder: product_index/)
    vectorstore.save_local("product_index")
