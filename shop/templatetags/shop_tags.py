from django import template
from django.forms.utils import flatatt
from django.utils.safestring import mark_safe

from shop.images import responsive_sources

register = template.Library()


@register.simple_tag
def product_card(product):
    variants = [v for v in product.variants.all() if v.is_active]
    if not variants:
        return {"price": None, "compare": None, "multiple": False, "tag": "", "sale": False}

    cheapest = min(variants, key=lambda v: v.price)
    in_stock = any(v.in_stock for v in variants)
    sale = any(v.compare_at_price and v.compare_at_price > v.price for v in variants)
    compare = (
        cheapest.compare_at_price
        if cheapest.compare_at_price and cheapest.compare_at_price > cheapest.price
        else None
    )

    if not in_stock:
        tag = "Ausverkauft"
    elif sale:
        tag = "Sale"
    else:
        tag = ""

    return {
        "price": cheapest.price,
        "compare": compare,
        "multiple": len({v.price for v in variants}) > 1,
        "tag": tag,
        "sale": sale and in_stock,
    }


@register.simple_tag
def responsive_image(field_file, alt="", sizes="100vw", css_class="", loading="lazy", fetchpriority=""):
    if not field_file:
        return ""

    sources = responsive_sources(field_file)
    attrs = {"alt": alt or "", "decoding": "async"}

    if sources:
        attrs["src"] = sources[-1][0]
        attrs["srcset"] = ", ".join(f"{url} {width}w" for url, width in sources)
        attrs["sizes"] = sizes
    else:
        attrs["src"] = field_file.url

    try:
        attrs["width"] = str(field_file.width)
        attrs["height"] = str(field_file.height)
    except (OSError, ValueError):
        pass

    if css_class:
        attrs["class"] = css_class
    if loading:
        attrs["loading"] = loading
    if fetchpriority:
        attrs["fetchpriority"] = fetchpriority

    return mark_safe(f"<img{flatatt(attrs)}>")
