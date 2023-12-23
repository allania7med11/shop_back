from core.models import Guest
from products.utils.orders import get_current_draft_order


class GuestMixin:
    def add_guest(self, request):
        self.guest = None
        guest_id = request.GET.get('guest_id')
        if guest_id:
            self.guest = Guest.objects.filter(guest_id=guest_id).first()
            
class CartInitiationMixin:
    def initiate_cart(self):
        self.cart = get_current_draft_order(self.guest, self.request.user)