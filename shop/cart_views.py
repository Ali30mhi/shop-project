from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
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
    else:
        messages.success(request, f"„{variant.product.name} – {variant.name}“ wurde in den Warenkorb gelegt.")
    return redirect("shop:cart")


@require_POST
def cart_update(request, variant_id):
    variant = _get_variant(variant_id)
    quantity = max(0, min(_to_int(request.POST.get("quantity"), 1), MAX_QUANTITY))
    Cart(request).set(variant, quantity)
    if quantity > variant.stock:
        messages.warning(request, f"Nur noch {variant.stock} Stück verfügbar – die Menge wurde angepasst.")
    return redirect("shop:cart")


@require_POST
def cart_remove(request, variant_id):
    Cart(request).remove(variant_id)
    messages.info(request, "Der Artikel wurde aus dem Warenkorb entfernt.")
    return redirect("shop:cart")