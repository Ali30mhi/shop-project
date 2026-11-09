from decimal import Decimal

from .models import ProductVariant

SESSION_KEY = "cart"


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.data = dict(self.session.get(SESSION_KEY, {}))

    def _save(self):
        self.session[SESSION_KEY] = self.data
        self.session.modified = True

    def quantity_of(self, variant):
        return self.data.get(str(variant.id), 0)

    def add(self, variant, quantity):
        self.set(variant, self.quantity_of(variant) + quantity)
        return self.quantity_of(variant)

    def set(self, variant, quantity):
        quantity = max(0, min(quantity, variant.stock))
        key = str(variant.id)
        if quantity:
            self.data[key] = quantity
        else:
            self.data.pop(key, None)
        self._save()

    def remove(self, variant_id):
        self.data.pop(str(variant_id), None)
        self._save()

    def clear(self):
        self.data = {}
        self._save()

    def __len__(self):
        return sum(self.data.values())

    def lines(self):
        variants = (
            ProductVariant.objects.filter(
                id__in=[int(key) for key in self.data],
                is_active=True,
                product__is_active=True,
            )
            .select_related("product")
            .prefetch_related("product__images")
        )
        lines = []
        cleaned = {}
        for variant in variants:
            quantity = min(self.data[str(variant.id)], variant.stock)
            if quantity <= 0:
                continue
            cleaned[str(variant.id)] = quantity
            lines.append({
                "variant": variant,
                "product": variant.product,
                "quantity": quantity,
                "line_total": variant.price * quantity,
            })
        if cleaned != self.data:
            self.data = cleaned
            self._save()
        return lines

    @staticmethod
    def total(lines):
        return sum((line["line_total"] for line in lines), Decimal("0"))