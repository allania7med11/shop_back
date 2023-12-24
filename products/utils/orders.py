from products.models import Order, OrderItems


def get_current_draft_order(request):
    if not request.user.is_authenticated:
        session_id = request.session.session_key
        if not session_id:
            # Create a new session if it doesn't exist
            request.session.create()
            session_id = request.session.session_key
        order, created = Order.objects.get_or_create(
            session_id=session_id,
            status=Order.OrderStatus.DRAFT,
        )
    else:
        user = request.user
        order, created = Order.objects.get_or_create(
            user=user,
            status=Order.OrderStatus.DRAFT,
            defaults={"total_amount": 0.0},
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
    