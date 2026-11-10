import stripe
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Category, Order, Product
from .seo import absolute_url, breadcrumb_jsonld, product_jsonld, website_jsonld

stripe.api_key = settings.STRIPE_SECRET_KEY


def _tpl(name):
    if getattr(settings, "SITE_THEME", "classic") == "ms":
        folder, file = name.rsplit("/", 1)
        return f"{folder}/ms_{file}"
    return name


def _catalog():
    return Product.objects.filter(is_active=True).prefetch_related("images", "variants")


@require_GET
def home(request):
    products = _catalog()
    return render(request, _tpl("shop/home.html"), {
        "products": products,
        "website_jsonld": website_jsonld(),
    })


@require_GET
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    return render(request, "shop/product_list.html", {
        "category": category,
        "products": _catalog().filter(category=category),
        "list_title": category.name,
        "list_intro": category.description,
        "breadcrumb_jsonld": breadcrumb_jsonld([
            ("Startseite", absolute_url("/")),
            (category.name, absolute_url(category.get_absolute_url())),
        ]),
    })


@require_GET
def search(request):
    query = " ".join(request.GET.get("q", "").split())[:80]
    products = []
    if query:
        products = _catalog().filter(
            Q(name__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
            | Q(variants__sku__iexact=query)
        ).distinct()
    return render(request, "shop/product_list.html", {
        "is_search": True,
        "search_query": query,
        "products": products,
        "list_title": "Suche",
    })


@require_GET
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    variants = list(product.active_variants)
    images = list(product.images.all())
    canonical_url = absolute_url(product.get_absolute_url())
    category = product.category if product.category and product.category.is_active else None
    crumbs = [("Startseite", absolute_url("/"))]
    if category:
        crumbs.append((category.name, absolute_url(category.get_absolute_url())))
    crumbs.append((product.name, canonical_url))

    return render(request, _tpl("shop/product_detail.html"), {
        "product": product,
        "category": category,
        "variants": variants,
        "images": images,
        "canonical_url": canonical_url,
        "og_image": absolute_url(images[0].image.url) if images else "",
        "product_jsonld": product_jsonld(product, variants, images),
        "breadcrumb_jsonld": breadcrumb_jsonld(crumbs),
    })


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /warenkorb/",
        "Disallow: /kasse/",
        "Disallow: /konto/",
        "Disallow: /suche/",
        "Disallow: /merkliste/",
        "",
        f"Sitemap: {absolute_url('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


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
                    "product_data": {"name": f"{item.product_name} ({item.variant_name})"},
                    "unit_amount": int(item.unit_price * 100),
                },
                "quantity": item.quantity,
            }
            for item in order.items.all()
        ],
        invoice_creation={"enabled": True},
        metadata={"order_id": str(order.id)},
        success_url=f"{settings.SITE_URL}/order/{order.id}/thanks/",
        cancel_url=f"{settings.SITE_URL}/warenkorb/",
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