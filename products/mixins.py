from core.models import Guest
from products.utils.orders import get_current_draft_order


class GuestMixin:
    def dispatch(self, request, *args, **kwargs):
        self.add_guest(request)
        return super().dispatch(request, *args, **kwargs)

    def add_guest(self, request):
        self.guest = None
        guest_id = request.GET.get('guest_id')

        if guest_id:
            self.guest = Guest.objects.filter(guest_id=guest_id).first()

class CartInitiationMixin:
    def dispatch(self, request, *args, **kwargs):
        self.initiate_cart()
        return super().dispatch(request, *args, **kwargs)

    def initiate_cart(self):
        self.cart = get_current_draft_order(self.guest, self.request.user)