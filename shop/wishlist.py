from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import Product, WishlistItem

SESSION_KEY = "wishlist"


class Wishlist:
    """Merkliste: ohne Login in der Sitzung, mit Login im Kundenkonto."""

    def __init__(self, request):
        self.session = request.session
        self.user = request.user if request.user.is_authenticated else None

    def ids(self):
        if self.user:
            return list(WishlistItem.objects.filter(user=self.user).values_list("product_id", flat=True))
        return list(self.session.get(SESSION_KEY, []))

    def toggle(self, product):
        """Merkt das Produkt oder entfernt es. True = steht jetzt auf der Merkliste."""
        if self.user:
            item, created = WishlistItem.objects.get_or_create(user=self.user, product=product)
            if not created:
                item.delete()
            return created
        ids = self.ids()
        added = product.id not in ids
        if added:
            ids.append(product.id)
        else:
            ids.remove(product.id)
        self.session[SESSION_KEY] = ids
        return added

    def products(self):
        return Product.objects.filter(is_active=True, id__in=self.ids()).prefetch_related("images", "variants")


@receiver(user_logged_in)
def merge_session_wishlist(sender, request, user, **kwargs):
    """Beim Anmelden: gemerkte Produkte aus der Sitzung ins Kundenkonto übernehmen."""
    session = getattr(request, "session", None)
    if session is None:
        return
    ids = session.pop(SESSION_KEY, [])
    for product in Product.objects.filter(id__in=ids):
        WishlistItem.objects.get_or_create(user=user, product=product)
