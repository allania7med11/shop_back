from django.db.models import F, Case, When, DecimalField
from rest_framework import viewsets
from products.filters import ProductFilter
from products.models import Category, Order, Product

from products.serializers import CategorySerializer, ProductSerializer
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Products to be viewed or edited.
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_class = ProductFilter
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            current_price=Case(
                When(
                    discount__isnull=False,
                    discount__active=True,
                    then=F("price") * (1 - F("discount__percent") / 100),
                ),
                default=F("price"),
                output_field=DecimalField(),
            )
        )
        return queryset


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Products to be viewed or edited.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]


class OrderAPIView(APIView):
    def post(self, request, *args, **kwargs):
        session_id = request.session.session_key
        if not session_id:
            # Create a new session if it doesn't exist
            request.session.create()
            session_id = request.session.session_key

        if not self.request.user.is_authenticated:
            user = None
        else:
            user = self.request.user

        # Use get_or_create to either retrieve an existing order for the user or create a new one
        Order.objects.get_or_create(
            session_id=session_id,
            user=user,
            status=Order.OrderStatus.DRAFT,
            defaults={"total_amount": 0.0},
        )

        # Return a response with only the status code
        return Response(status=status.HTTP_201_CREATED)
