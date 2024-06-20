import uuid
from products.models import Order, OrderAddress, OrderItems


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
    user_order = Order.objects.filter(user=user,status=Order.OrderStatus.DRAFT).first()
    if session_order:
        if not user_order:
            session_order.uuid = None
            session_order.user = user
            session_order.save()
            return session_order
        merge_orders(user_order, session_order)
        session_order.delete()
        return user_order
    if user_order:
        return user_order
    order = Order.objects.create(
        user=user,
        status=Order.OrderStatus.DRAFT,
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
        # If the same product already exists in the current order, update the quantity and subtotal
        existing_item.quantity += item.quantity
        existing_item.save()
    else:
        # If the product does not exist in the current order, create a new order item
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
    order.set_total_amount()
