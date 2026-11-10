"""Legt drei Beispiel-Kategorien an und ordnet die Demo-Produkte zu.

Ausführen:
    python manage.py shell < scripts/demo_categories.py
Kann beliebig oft ausgeführt werden.
"""
from shop.models import Category, Product

CATEGORIES = [
    ("accessoires", "Accessoires", "Taschen und Begleiter für jeden Tag.", ["umhaengetasche-saddle"]),
    ("wohnen-deko", "Wohnen & Deko", "Vasen und Deko für ein ruhiges Zuhause.", ["keramikvase-salbei"]),
    ("duefte", "Düfte", "Parfums mit Charakter.", ["eau-de-parfum-ambra"]),
]

for order, (slug, name, description, product_slugs) in enumerate(CATEGORIES, start=1):
    category, _ = Category.objects.update_or_create(
        slug=slug,
        defaults={"name": name, "description": description, "sort_order": order, "is_active": True},
    )
    count = Product.objects.filter(slug__in=product_slugs).update(category=category)
    print("OK:", category.name, "-", count, "Produkt(e)")
