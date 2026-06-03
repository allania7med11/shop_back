from authentication.utils import get_actor
from products.models import Order, OrderAddress, OrderItems, Payment


def get_current_draft_order(request):
    """The current draft order (cart) for whoever is acting — guest or registered user.

    Resolves the actor via ``get_actor`` and delegates to ``get_draft_order``, so the HTTP
    cart and the AI assistant key on the SAME user-scoped order (Option B). The old
    ``order_uuid``/``user=None`` guest path is gone — it was the source of the divergence
    (the cart page showing empty while the assistant saw items). Guest→user cart merging
    now happens once, on login/registration, in the ``user_logged_in`` handler.
    """
    return get_draft_order(get_actor(request))


def get_draft_order(user):
    """Get (or create) the draft order scoped strictly to ``user`` (a real or guest User).

    Single, request-free cart resolver shared by the HTTP layer (via
    ``get_current_draft_order``) and the AI assistant (which only has the chat owner).
    """
    order = Order.objects.filter(user=user, status=Order.OrderStatus.DRAFT).first()
    if not order:
        order = Order.objects.create(user=user, status=Order.OrderStatus.DRAFT)
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


def migrate_guest_cart_to_user(guest_user, user):
    """Move the guest's draft cart onto a real user on login/registration.

    If the user already has a draft cart, merge the guest's items into it (``merge_orders``
    dedupes by product and sums quantity) and drop the guest order; otherwise just reassign
    the guest order to the user. Handles both new and pre-existing accounts.
    """
    guest_order = Order.objects.filter(
        user=guest_user.user, status=Order.OrderStatus.DRAFT
    ).first()
    if not guest_order:
        return

    user_order = Order.objects.filter(user=user, status=Order.OrderStatus.DRAFT).first()
    if not user_order:
        guest_order.user = user
        guest_order.save()
        return

    merge_orders(user_order, guest_order)
    guest_order.delete()


def merge_orders(current_order: Order, other_order: Order):
    # Check if both orders are in draft status
    if not (current_order.is_draft() and other_order.is_draft()):
        raise ValueError("Orders cannot be merged as both must be in draft status.")

    # Merge order items
    for item in other_order.items.all():
        merge_order_item(current_order, item)


def merge_order_item(current_order: Order, item: OrderItems):
    existing_item: OrderItems = current_order.items.filter(product=item.product).first()
    if existing_item:
        # If the same product already exists in the current order, update the
        # quantity and subtotal
        existing_item.quantity += item.quantity
        existing_item.save()
    else:
        # If the product does not exist in the current order, create a new
        # order item
        item.order = current_order
        item.save()


def get_existing_or_new_order_address(order, address_data):
    try:
        address = OrderAddress.objects.get(order=order)
    except OrderAddress.DoesNotExist:
        address = OrderAddress(order=order, **address_data)
    return address


def set_order_to_processing(order: Order):
    order.status = Order.PROCESSING
    order.save()


def set_payment_to_succeeded(payment: Payment):
    payment.status = Payment.SUCCEEDED
    payment.save()
