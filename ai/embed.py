from django.utils.html import strip_tags
from djmoney.money import Money
from langchain.schema import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from products.models import Category, Product


def build_product_documents():
    """
    Converts all products from the DB into LangChain Documents.
    These will be used to build a searchable vector index.
    """
    docs = []
    products = Product.objects.select_related("category").all()

    for product in products:
        price: Money = product.price
        price_str = f"{price.amount} {price.currency}"  # Clean price
        clean_description = strip_tags(product.description.html)
        content = f"{product.name}\n{clean_description}\nPrice: {price_str}"
        category: Category = product.category
        metadata = {
            "product_slug": product.slug,
            "category_slug": category.slug,
            "category_name": category.name,
        }
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
