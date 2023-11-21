from products.utils.orders import get_current_draft_order


class CartInitiationMixin:
    def dispatch(self, request, *args, **kwargs):
        self.initiate_cart(request)
        return super().dispatch(request, *args, **kwargs)

    def initiate_cart(self, request):
        self.cart = get_current_draft_order(request)