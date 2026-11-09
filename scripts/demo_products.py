from decimal import Decimal as D
from pathlib import Path

from django.core.files import File

from shop.models import Product, ProductImage, ProductVariant

SRC = Path.home() / "Downloads" / "produkte"


def image_path(stem):
    for ext in ("jpg", "jpeg", "png", "webp"):
        candidate = SRC / f"{stem}.{ext}"
        if candidate.exists():
            return candidate
    raise SystemExit(f"Bild nicht gefunden: {SRC}/{stem}.jpg")


PRODUCTS = [
    {
        "slug": "eau-de-parfum-ambra",
        "name": "Eau de Parfum Ambra",
        "short": "Warm, holzig und langanhaltend – im klassischen Bernsteinflakon.",
        "description": (
            "Ambra verbindet warme Bernsteinnoten mit einem Hauch Vanille und sanftem Zedernholz. "
            "Ein Duft für jeden Tag, der lange auf der Haut bleibt, ohne aufdringlich zu wirken.\n\n"
            "Der schwere Glasflakon mit schwarzem Verschluss ist ein Blickfang auf jeder Kommode."
        ),
        "image": "parfum",
        "alt": "Eau de Parfum Ambra im bernsteinfarbenen Glasflakon mit schwarzem Verschluss",
        "variants": [
            {"size": "50 ml", "sku": "AMB-50", "price": D("59.00"), "stock": 12},
            {"size": "100 ml", "sku": "AMB-100", "price": D("89.00"), "stock": 6},
        ],
    },
    {
        "slug": "keramikvase-salbei",
        "name": "Keramikvase Salbei",
        "short": "Glasierte Keramik mit matter Oberfläche – wunderschön mit Trockenblumen.",
        "description": (
            "Die bauchige Form und die samtig matte Glasur machen diese Vase zu einem ruhigen "
            "Mittelpunkt in jedem Raum. Ideal für Trockengräser und Pampas.\n\n"
            "Höhe ca. 20 cm, Durchmesser ca. 15 cm."
        ),
        "image": "vase",
        "alt": "Salbeigrüne Keramikvase mit getrockneten Gräsern vor hellem Hintergrund",
        "variants": [
            {"color_name": "Salbeigrün", "color_hex": "#7A8466", "sku": "VASE-SAL",
             "price": D("34.90"), "compare_at_price": D("39.90"), "stock": 8},
            {"color_name": "Sand", "color_hex": "#D8C7A8", "sku": "VASE-SAND",
             "price": D("34.90"), "compare_at_price": D("39.90"), "stock": 4},
            {"color_name": "Anthrazit", "color_hex": "#3B3B3B", "sku": "VASE-ANT",
             "price": D("34.90"), "compare_at_price": D("39.90"), "stock": 0},
        ],
    },
    {
        "slug": "umhaengetasche-saddle",
        "name": "Umhängetasche Saddle",
        "short": "Zeitlose Crossbody-Tasche mit Schnallenverschluss und verstellbarem Riemen.",
        "description": (
            "Die Saddle Bag ist kompakt genug für den Alltag und bietet trotzdem Platz für "
            "Smartphone, Geldbörse und Schlüssel. Der breite Riemen ist verstellbar, die Schnalle "
            "setzt einen eleganten Akzent.\n\n"
            "Maße ca. 24 × 18 × 8 cm. Material: Lederoptik."
        ),
        "image": "tasche",
        "alt": "Cognacfarbene Umhängetasche mit Schnallenverschluss und Schulterriemen",
        "variants": [
            {"color_name": "Cognac", "color_hex": "#9A5B2E", "sku": "SAD-COG", "price": D("129.00"), "stock": 5},
            {"color_name": "Schwarz", "color_hex": "#1F1F1F", "sku": "SAD-BLK", "price": D("129.00"), "stock": 3},
            {"color_name": "Olivgrün", "color_hex": "#556B2F", "sku": "SAD-OLV", "price": D("129.00"), "stock": 2},
        ],
    },
]

for data in PRODUCTS:
    product, _ = Product.objects.get_or_create(slug=data["slug"], defaults={"name": data["name"]})
    product.name = data["name"]
    product.short_description = data["short"]
    product.description = data["description"]
    product.is_active = True
    product.save()

    product.variants.all().delete()
    product.images.all().delete()

    for order, variant in enumerate(data["variants"], start=1):
        ProductVariant.objects.create(product=product, sort_order=order, **variant)

    path = image_path(data["image"])
    with path.open("rb") as fh:
        ProductImage.objects.create(product=product, alt_text=data["alt"], image=File(fh, name=path.name))

    print("OK:", product.name, "-", product.variants.count(), "Varianten")

Product.objects.filter(slug="test-product").update(is_active=False)
print("Test Product deaktiviert.")
