from rest_framework import viewsets
from products.models import Category, Product

from products.serializers import CategorySerializer, ProductSerializer
from rest_framework import permissions

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Products to be viewed or edited.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Products to be viewed or edited.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]