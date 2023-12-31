import uuid
from products.models import Order, OrderItems


def get_current_draft_order(request):
    session_order = get_session_order(request)
    if not request.user.is_authenticated:
        if session_order:
            return session_order
        order_uuid = request.session.get("order_uuid")
        if not order_uuid:
            order_uuid = str(uuid.uuid4())  # Use a new UUID for the order_uuid
            request.session["order_uuid"] = order_uuid
        order = Order.objects.create(
            uuid=order_uuid,
            status=Order.OrderStatus.DRAFT,
        )
        return order
    user = request.user
    if session_order:
        session_order.uuid = None
        session_order.user = user
        session_order.save()
        return session_order
    order, created = Order.objects.get_or_create(
        user=user,
        status=Order.OrderStatus.DRAFT,
        defaults={"total_amount": 0.0},
    )
    return order

def get_session_order(request):
    order_uuid = request.session.get("order_uuid")
    if order_uuid:
        order = Order.objects.filter(
            uuid=order_uuid,
            status=Order.OrderStatus.DRAFT,
        ).first()
        return order
    return None


def get_existing_or_new_order_item(order, product):
    """
    Get an instance of an existing item with the same order and product, or else
    return an instance of an order_item associated with the provided order.
    """
    instance = OrderItems.objects.filter(order=order, product=product).first()
    if not instance:
        instance = OrderItems(order=order)
    return instance
    