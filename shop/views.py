import stripe
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY


@require_POST
def start_checkout(request, order_id):
    order = get_object_or_404(Order, id=order_id, status=Order.Status.PENDING)
    session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=order.email,
        line_items=[
            {
                "price_data": {
                    "currency": order.currency,
                    "product_data": {"name": item.product_name},
                    "unit_amount": int(item.unit_price * 100),
                },
                "quantity": item.quantity,
            }
            for item in order.items.all()
        ],
        invoice_creation={"enabled": True},
        metadata={"order_id": str(order.id)},
        success_url=f"{settings.SITE_URL}/order/{order.id}/thanks/",
        cancel_url=f"{settings.SITE_URL}/cart/",
    )
    order.stripe_session_id = session.id
    order.save(update_fields=["stripe_session_id"])
    return redirect(session.url, code=303)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            request.META.get("HTTP_STRIPE_SIGNATURE", ""),
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse(status=400)

    if event.type == "checkout.session.completed":
        session = event.data.object
        if session.payment_status == "paid":
            mark_order_paid(session.metadata["order_id"])

    return HttpResponse(status=200)


def mark_order_paid(order_id):
    with transaction.atomic():
        order = Order.objects.select_for_update().get(id=order_id)
        if order.status != Order.Status.PENDING:
            return
        order.status = Order.Status.PAID
        order.paid_at = timezone.now()
        order.save(update_fields=["status", "paid_at"])
