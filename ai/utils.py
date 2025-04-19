"""
Utility functions for AI-related operations.
"""

# Vector index paths
VECTOR_INDEXES_DIR = "/vector_indexes"
PRODUCTS_INDEX_PATH = f"{VECTOR_INDEXES_DIR}/products"


def get_products_index_path():
    """
    Returns the path to the products vector index.
    """
    return PRODUCTS_INDEX_PATH
