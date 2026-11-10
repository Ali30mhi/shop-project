from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

HEX_COLOR = RegexValidator(
    r"^#[0-9A-Fa-f]{6}$",
    "Bitte einen Farbcode im Format #RRGGBB eingeben, z. B. #556B2F.",
)


class Category(models.Model):
    name = models.CharField("Name", max_length=100)
    slug = models.SlugField(
        "URL-Kürzel", max_length=120, unique=True, blank=True,
        help_text="Wird automatisch aus dem Namen erzeugt.",
    )
    description = models.CharField(
        "Kurzbeschreibung", max_length=200, blank=True,
        help_text="Erscheint auf der Kategorie-Kachel und auf der Kategorieseite.",
    )
    sort_order = models.PositiveIntegerField("Reihenfolge", default=0)
    is_active = models.BooleanField(
        "Aktiv", default=True,
        help_text="Kategorien ohne aktive Produkte werden im Shop nicht angezeigt.",
    )

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Kategorie"
        verbose_name_plural = "Kategorien"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:category", args=[self.slug])


class Product(models.Model):
    name = models.CharField("Name", max_length=200)
    slug = models.SlugField(
        "URL-Kürzel", max_length=220, unique=True, blank=True,
        help_text="Wird automatisch aus dem Namen erzeugt.",
    )
    category = models.ForeignKey(
        Category, verbose_name="Kategorie", related_name="products",
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    short_description = models.CharField("Kurzbeschreibung", max_length=300, blank=True)
    description = models.TextField("Beschreibung", blank=True)
    size_guide = models.TextField(
        "Größe & Maße", blank=True,
        help_text="Maße, Größentabelle oder Pflegehinweise – erscheint als eigener Abschnitt.",
    )
    meta_title = models.CharField(
        "SEO-Titel", max_length=70, blank=True,
        help_text="Titel in den Google-Ergebnissen (ca. 60 Zeichen). Leer = Produktname.",
    )
    meta_description = models.CharField(
        "SEO-Beschreibung", max_length=160, blank=True,
        help_text="Text in den Google-Ergebnissen (ca. 150 Zeichen). Leer = Kurzbeschreibung.",
    )
    is_active = models.BooleanField(
        "Aktiv", default=True, help_text="Deaktivierte Produkte sind im Shop nicht sichtbar.",
    )
    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Geändert am", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Produkt"
        verbose_name_plural = "Produkte"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:product_detail", args=[self.slug])

    @property
    def seo_title(self):
        return self.meta_title or self.name

    @property
    def seo_description(self):
        return self.meta_description or self.short_description

    @property
    def active_variants(self):
        return self.variants.filter(is_active=True)

    @property
    def min_price(self):
        variant = self.active_variants.order_by("price").first()
        return variant.price if variant else None

    @property
    def main_image(self):
        return self.images.first()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, verbose_name="Produkt", related_name="images", on_delete=models.CASCADE)
    image = models.ImageField("Bild", upload_to="products/%Y/%m/")
    alt_text = models.CharField(
        "Alt-Text", max_length=200,
        help_text="Kurze Bildbeschreibung für Google und Screenreader.",
    )
    sort_order = models.PositiveIntegerField("Reihenfolge", default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Produktbild"
        verbose_name_plural = "Produktbilder"

    def __str__(self):
        return self.alt_text


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, verbose_name="Produkt", related_name="variants", on_delete=models.CASCADE)
    color_name = models.CharField("Farbe", max_length=50, blank=True, help_text="z. B. Olivgrün")
    color_hex = models.CharField(
        "Farbcode", max_length=7, blank=True, validators=[HEX_COLOR], help_text="z. B. #556B2F",
    )
    size = models.CharField("Größe", max_length=30, blank=True, help_text="z. B. M oder 42")
    name = models.CharField(
        "Bezeichnung", max_length=100, blank=True,
        help_text="Optional. Leer = wird aus Farbe und Größe erzeugt.",
    )
    sku = models.CharField("Artikelnummer (SKU)", max_length=64, unique=True)
    price = models.DecimalField(
        "Preis (€)", max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    compare_at_price = models.DecimalField(
        "Streichpreis (€)", max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Alter Preis, wird durchgestrichen angezeigt. Leer lassen, wenn kein Rabatt.",
    )
    stock = models.PositiveIntegerField("Lagerbestand", default=0)
    is_active = models.BooleanField("Aktiv", default=True)
    sort_order = models.PositiveIntegerField("Reihenfolge", default=0)

    class Meta:
        ordering = ["sort_order", "price"]
        verbose_name = "Variante"
        verbose_name_plural = "Varianten"

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = " / ".join(part for part in (self.color_name, self.size) if part) or self.sku
        super().save(*args, **kwargs)

    @property
    def in_stock(self):
        return self.stock > 0


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Zahlung ausstehend"
        PAID = "paid", "Bezahlt"
        SHIPPED = "shipped", "Versendet"
        CANCELLED = "cancelled", "Storniert"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Kundenkonto",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="orders",
    )
    email = models.EmailField("E-Mail")
    full_name = models.CharField("Name", max_length=200, blank=True)
    phone = models.CharField("Telefon", max_length=30, blank=True)
    shipping_address = models.TextField("Lieferadresse", blank=True)
    currency = models.CharField("Währung", max_length=3, default="eur")
    total = models.DecimalField("Gesamtbetrag", max_digits=10, decimal_places=2, default=Decimal("0"))
    status = models.CharField("Status", max_length=10, choices=Status.choices, default=Status.PENDING)

    stripe_session_id = models.CharField("Stripe-Session-ID", max_length=255, blank=True, db_index=True)
    stripe_invoice_id = models.CharField("Stripe-Rechnungs-ID", max_length=255, blank=True)
    invoice_number = models.CharField("Rechnungsnummer", max_length=100, blank=True)
    invoice_url = models.URLField("Rechnung (online)", max_length=500, blank=True)
    invoice_pdf_url = models.URLField("Rechnung (PDF)", max_length=500, blank=True)

    created_at = models.DateTimeField("Bestellt am", auto_now_add=True)
    paid_at = models.DateTimeField("Bezahlt am", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Bestellung"
        verbose_name_plural = "Bestellungen"

    def __str__(self):
        return f"Bestellung #{self.pk}"

    def recalculate_total(self):
        self.total = sum((item.line_total for item in self.items.all()), Decimal("0"))


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name="Bestellung", related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant, verbose_name="Variante",
        null=True, blank=True, on_delete=models.SET_NULL, related_name="order_items",
    )
    product_name = models.CharField("Produkt", max_length=200)
    variant_name = models.CharField("Variante (Name)", max_length=100, blank=True)
    sku = models.CharField("SKU", max_length=64, blank=True)
    unit_price = models.DecimalField("Einzelpreis", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("Menge", default=1)

    class Meta:
        verbose_name = "Position"
        verbose_name_plural = "Positionen"

    def __str__(self):
        return f"{self.quantity} x {self.product_name} ({self.variant_name})"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
