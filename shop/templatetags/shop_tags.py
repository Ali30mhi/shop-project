from django import template

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
