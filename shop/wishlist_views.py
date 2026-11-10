from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from .models import Product
from .wishlist import Wishlist


@require_GET
def wishlist_detail(request):
    return render(request, "shop/product_list.html", {
        "is_wishlist": True,
        "products": Wishlist(request).products(),
        "list_title": "Merkliste",
    })


@require_POST
def wishlist_toggle(request):
    try:
        product_id = int(request.POST.get("product", ""))
    except ValueError:
        product_id = 0
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if Wishlist(request).toggle(product):
        messages.success(request, f"„{product.name}“ steht jetzt auf Ihrer Merkliste.")
    else:
        messages.info(request, f"„{product.name}“ wurde von der Merkliste entfernt.")
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        return redirect(target)
    return redirect("shop:wishlist")
