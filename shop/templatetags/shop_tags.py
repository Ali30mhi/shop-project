from django import template
from django.forms.utils import flatatt
from django.utils.safestring import mark_safe

from shop.images import responsive_sources

register = template.Library()

FALLBACK_SWATCH = "#d9ddd6"


def _unique_colors(variants):
    colors, seen = [], set()
    for v in variants:
        if v.color_name and v.color_name not in seen:
            seen.add(v.color_name)
            colors.append({"name": v.color_name, "hex": v.color_hex or FALLBACK_SWATCH})
    return colors


@register.simple_tag
def product_card(product):
    variants = [v for v in product.variants.all() if v.is_active]
    if not variants:
        return {"price": None, "compare": None, "multiple": False, "tag": "", "sale": False,
                "colors": [], "more_colors": 0, "quick_variant": None}

    cheapest = min(variants, key=lambda v: v.price)
    in_stock = any(v.in_stock for v in variants)
    sale = any(v.compare_at_price and v.compare_at_price > v.price for v in variants)
    compare = (
        cheapest.compare_at_price
        if cheapest.compare_at_price and cheapest.compare_at_price > cheapest.price
        else None
    )
    colors = _unique_colors(variants)

    if not in_stock:
        tag = "Ausverkauft"
    elif sale:
        tag = "Sale"
    else:
        tag = ""

    quick_variant = variants[0] if len(variants) == 1 and variants[0].in_stock else None

    return {
        "price": cheapest.price,
        "compare": compare,
        "multiple": len({v.price for v in variants}) > 1,
        "tag": tag,
        "sale": sale and in_stock,
        "colors": colors[:5],
        "more_colors": max(len(colors) - 5, 0),
        "quick_variant": quick_variant,
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
    return {
        "colors": colors,
        "sizes": sizes,
        "data": data,
        "enabled": (uses_color or uses_size) and consistent,
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
