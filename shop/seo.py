import json

from django.conf import settings
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe


def absolute_url(path):
    return settings.SITE_URL.rstrip("/") + path


def to_jsonld(data):
    raw = json.dumps(data, ensure_ascii=False)
    raw = raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(raw)


def website_jsonld():
    return to_jsonld({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": settings.SITE_NAME,
        "url": absolute_url("/"),
    })


def product_jsonld(product, variants, images):
    url = absolute_url(product.get_absolute_url())
    description = product.seo_description or strip_tags(product.description)[:500]
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "description": description,
        "url": url,
        "image": [absolute_url(img.image.url) for img in images],
        "offers": [
            {
                "@type": "Offer",
                "sku": variant.sku,
                "name": variant.name,
                "price": f"{variant.price:.2f}",
                "priceCurrency": settings.SHOP_CURRENCY.upper(),
                "availability": (
                    "https://schema.org/InStock" if variant.in_stock else "https://schema.org/OutOfStock"
                ),
                "itemCondition": "https://schema.org/NewCondition",
                "url": url,
            }
            for variant in variants
        ],
    }
    if variants:
        data["sku"] = variants[0].sku
    return to_jsonld(data)


def breadcrumb_jsonld(items):
    return to_jsonld({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": position, "name": name, "item": url}
            for position, (name, url) in enumerate(items, start=1)
        ],
    })