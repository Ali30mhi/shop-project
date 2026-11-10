from decimal import Decimal

from django.db.models import Count
from django.utils.functional import SimpleLazyObject

from pages.models import StoreSettings

from .cart import Cart
from .models import Category


def visible_categories():
    return (
        Category.objects.filter(is_active=True, products__is_active=True)
        .annotate(product_count=Count("products"))
        .order_by("sort_order", "name")
    )


def catalog(request):
    # Lazy: die Abfrage läuft nur, wenn ein Template die Kategorien wirklich nutzt.
    return {"nav_categories": SimpleLazyObject(lambda: list(visible_categories()))}


def cart(request):
    cart = Cart(request)
    lines = cart.lines() if cart.data else []
    total = cart.total(lines)
    store = StoreSettings.for_request(request)

    context = {
        "cart_count": sum(line["quantity"] for line in lines),
        "cart_lines": lines,
        "cart_total": total,
        "cart_shipping": None,
        "cart_grand_total": total,
        "open_cart_drawer": bool(request.session.pop("open_cart_drawer", False)),
        "free_shipping_threshold": None,
    }

    qualifies_for_free_shipping = False
    threshold = store.free_shipping_threshold
    if threshold and threshold > 0:
        remaining = max(threshold - total, Decimal("0"))
        qualifies_for_free_shipping = remaining == 0
        context.update({
            "free_shipping_threshold": threshold,
            "free_shipping_remaining": remaining,
            "free_shipping_percent": int(min(total / threshold * 100, Decimal("100"))),
        })

    if lines and store.shipping_cost is not None:
        shipping = Decimal("0") if qualifies_for_free_shipping else store.shipping_cost
        context["cart_shipping"] = shipping
        context["cart_grand_total"] = total + shipping

    return context
