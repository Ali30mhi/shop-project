from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from .cart import Cart
from .models import ProductVariant

MAX_QUANTITY = 99


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_variant(variant_id):
    return get_object_or_404(
        ProductVariant.objects.select_related("product"),
        id=variant_id,
        is_active=True,
        product__is_active=True,
    )


def _back(request):
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        request.session["open_cart_drawer"] = True
        return redirect(target)
    return redirect("shop:cart")


@require_GET
def cart_detail(request):
    cart = Cart(request)
    lines = cart.lines()
    return render(request, "shop/cart.html", {"lines": lines, "total": cart.total(lines)})


@require_POST
def cart_add(request):
    variant = _get_variant(_to_int(request.POST.get("variant"), 0))
    quantity = max(1, min(_to_int(request.POST.get("quantity"), 1), MAX_QUANTITY))

    if not variant.in_stock:
        messages.error(request, "Diese Variante ist leider ausverkauft.")
        return redirect(variant.product.get_absolute_url())

    cart = Cart(request)
    before = cart.quantity_of(variant)
    after = cart.add(variant, quantity)

    if after == before:
        messages.warning(request, "Die maximal verfügbare Menge befindet sich bereits im Warenkorb.")
    elif after < before + quantity:
        messages.warning(request, f"Nur noch {variant.stock} Stück verfügbar – die Menge wurde angepasst.")
    return _back(request)


@require_POST
def cart_update(request, variant_id):
    variant = _get_variant(variant_id)
    quantity = max(0, min(_to_int(request.POST.get("quantity"), 1), MAX_QUANTITY))
    Cart(request).set(variant, quantity)
    if quantity > variant.stock:
        messages.warning(request, f"Nur noch {variant.stock} Stück verfügbar – die Menge wurde angepasst.")
    return _back(request)


@require_POST
def cart_remove(request, variant_id):
    Cart(request).remove(variant_id)
    return _back(request)
