from core.models import Guest
from products.models import Order, OrderItems


def get_current_draft_order(user, guest_id=None):
    order = None
    if user and user.is_authenticated:
        order, created = Order.objects.get_or_create(
            user=user,
            status=Order.OrderStatus.DRAFT,
            defaults={"total_amount": 0.0},
        )
    elif guest_id:
        guest = Guest.objects.filter(guest_id=guest_id).first() 
        if guest:
            order, created = Order.objects.get_or_create(
                guest=guest,
                status=Order.OrderStatus.DRAFT,
            )
    return order


def get_existing_or_new_order_item(order, product):
    """
    Get an instance of an existing item with the same order and product, or else
    return an instance of an order_item associated with the provided order.
    """
    instance = OrderItems.objects.filter(order=order, product=product).first()
    if not instance:
        instance = OrderItems(order=order)
    return instance
    