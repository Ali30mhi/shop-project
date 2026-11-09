from datetime import timedelta

from django import template
from django.forms.utils import flatatt
from django.utils import timezone
from django.utils.safestring import mark_safe

from shop.images import responsive_sources
from shop.models import Product, ProductVariant

register = template.Library()

FALLBACK_SWATCH = "#d9ddd6"
NEW_DAYS = 30


def _unique_colors(variants):
    colors, seen = [], set()
    for v in variants:
        if v.color_name and v.color_name not in seen:
            seen.add(v.color_name)
            colors.append({"name": v.color_name, "hex": v.color_hex or FALLBACK_SWATCH})
    return colors


def _discount(price, compare):
    if compare and compare > price:
        return int(round((compare - price) / compare * 100))
    return 0


@register.simple_tag
def product_card(product):
    variants = [v for v in product.variants.all() if v.is_active]
    if not variants:
        return {"price": None, "compare": None, "multiple": False, "tag": "", "sale": False,
                "colors": [], "more_colors": 0, "quick_variant": None,
                "badge": "", "badge_label": "", "discount": 0, "low_stock": 0}

    cheapest = min(variants, key=lambda v: v.price)
    in_stock = any(v.in_stock for v in variants)
    sale = any(v.compare_at_price and v.compare_at_price > v.price for v in variants)
    compare = cheapest.compare_at_price if _discount(cheapest.price, cheapest.compare_at_price) else None
    colors = _unique_colors(variants)
    total_stock = sum(v.stock for v in variants)
    is_new = product.created_at and product.created_at >= timezone.now() - timedelta(days=NEW_DAYS)

    if not in_stock:
        tag, badge, badge_label = "Ausverkauft", "soldout", "Ausverkauft"
    elif sale:
        tag, badge, badge_label = "Sale", "sale", "Sale"
    elif is_new:
        tag, badge, badge_label = "", "new", "Neu"
    else:
        tag, badge, badge_label = "", "", ""

    return {
        "price": cheapest.price,
        "compare": compare,
        "multiple": len({v.price for v in variants}) > 1,
        "tag": tag,
        "sale": sale and in_stock,
        "colors": colors[:5],
        "more_colors": max(len(colors) - 5, 0),
        "quick_variant": variants[0] if len(variants) == 1 and variants[0].in_stock else None,
        "badge": badge,
        "badge_label": badge_label,
        "discount": max((_discount(v.price, v.compare_at_price) for v in variants), default=0),
        "low_stock": total_stock if 0 < total_stock <= 3 else 0,
    }


@register.simple_tag
def variant_options(variants):
    variants = list(variants)
    colors = _unique_colors(variants)
    sizes, seen_sizes, combos, data = [], set(), set(), []

    for v in variants:
        if v.size and v.size not in seen_sizes:
            seen_sizes.add(v.size)
            sizes.append(v.size)
        combos.add((v.color_name, v.size))
        data.append({
            "id": v.id,
            "color": v.color_name,
            "size": v.size,
            "price": str(v.price),
            "compare": str(v.compare_at_price) if v.compare_at_price else "",
            "inStock": v.in_stock,
            "lowStock": v.stock if 0 < v.stock <= 3 else None,
        })

    uses_color, uses_size = bool(colors), bool(sizes)
    consistent = (
        (not uses_color or all(v.color_name for v in variants))
        and (not uses_size or all(v.size for v in variants))
        and len(combos) == len(variants)
    )
    return {"colors": colors, "sizes": sizes, "data": data, "enabled": (uses_color or uses_size) and consistent}


@register.simple_tag
def related_products(product, limit=4):
    return list(
        Product.objects.filter(is_active=True).exclude(pk=product.pk).prefetch_related("images", "variants")[:limit]
    )


@register.simple_tag
def max_discount():
    best = 0
    for v in ProductVariant.objects.filter(is_active=True, product__is_active=True, compare_at_price__isnull=False):
        best = max(best, _discount(v.price, v.compare_at_price))
    return best


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
