from products.models import Order


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
            defaults={"total_amount": 0.0},
        )
    else:
        user = request.user
        order, created = Order.objects.get_or_create(
            session_id=session_id,
            user=user,
            status=Order.OrderStatus.DRAFT,
            defaults={"total_amount": 0.0},
        )
    return order
