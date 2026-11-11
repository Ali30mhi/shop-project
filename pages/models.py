from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe

from . import branding


class Page(models.Model):
    title = models.CharField("Titel", max_length=200)
    slug = models.SlugField("URL-Kürzel", max_length=100, unique=True)
    body = models.TextField(
        "Inhalt", blank=True,
        help_text="Text oder HTML. Rechtstexte aus einem Generator können direkt eingefügt werden.",
    )
    meta_description = models.CharField("SEO-Beschreibung", max_length=160, blank=True)
    show_in_footer = models.BooleanField("Im Footer anzeigen", default=True)
    footer_order = models.PositiveIntegerField("Reihenfolge im Footer", default=0)
    updated_at = models.DateTimeField("Zuletzt geändert", auto_now=True)

    class Meta:
        ordering = ["footer_order", "title"]
        verbose_name = "Seite"
        verbose_name_plural = "Seiten"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("pages:detail", args=[self.slug])

    @property
    def rendered_body(self):
        if "<" in self.body:
            return mark_safe(self.body)
        return mark_safe(linebreaks(self.body, autoescape=True))


class StoreSettings(models.Model):
    logo = models.ImageField(
        "Logo", upload_to="site/", blank=True,
        help_text="PNG oder WebP mit transparentem Hintergrund, Querformat, mindestens 80 px hoch. "
                  "Leer = Buchstaben-Logo mit dem Shopnamen.",
    )
    logo_dark = models.ImageField(
        "Logo für dunklen Hintergrund", upload_to="site/", blank=True,
        help_text="Optional: helle Variante für das dunkle Design und den Footer. "
                  "Leer = das Logo wird dort auf einer weißen Fläche gezeigt.",
    )
    favicon = models.ImageField(
        "Favicon (Symbol im Browser-Tab)", upload_to="site/", blank=True,
        help_text="Quadratisches PNG, mindestens 180 × 180 px. "
                  "Leer = farbiges Quadrat mit dem ersten Buchstaben des Shopnamens.",
    )
    brand_color = models.CharField(
        "Markenfarbe", max_length=7, default=branding.DEFAULT_COLOR,
        validators=[RegexValidator(r"^#[0-9a-fA-F]{6}$", "Bitte eine Farbe im Format #rrggbb angeben.")],
        help_text="Farbe für Buttons, Links und Akzente. Schriftfarbe und dunkles Design "
                  "werden automatisch passend berechnet. Standard: #db3012 (Orange).",
    )

    announcement = models.CharField(
        "Hinweisleiste", max_length=200, blank=True,
        default="Sichere Zahlung · Schneller Versand · 14 Tage Widerrufsrecht",
    )
    hero_eyebrow = models.CharField("Hero: Überzeile", max_length=80, blank=True, default="Neue Kollektion")
    hero_title = models.CharField(
        "Hero: Überschrift", max_length=120, default="Einfache Dinge, die jeden Tag begleiten",
    )
    hero_text = models.TextField(
        "Hero: Text", blank=True,
        default="Praktische, sorgfältig gefertigte Produkte mit zeitlosem Design – Qualität, die Sie jeden Tag begleitet.",
    )
    hero_button = models.CharField("Hero: Button-Text", max_length=40, default="Produkte entdecken")
    hero_image = models.ImageField(
        "Hero: Bild", upload_to="site/", blank=True, help_text="Hochformat oder quadratisch, mindestens 1200 px breit.",
    )
    hero_image_alt = models.CharField("Hero: Alt-Text des Bildes", max_length=200, blank=True)

    benefit_1_title = models.CharField("Vorteil 1: Titel", max_length=60, default="Schneller Versand")
    benefit_1_text = models.CharField(
        "Vorteil 1: Text", max_length=120, blank=True, default="Sorgfältig verpackt und zuverlässig zugestellt",
    )
    benefit_2_title = models.CharField("Vorteil 2: Titel", max_length=60, default="14 Tage Widerrufsrecht")
    benefit_2_text = models.CharField(
        "Vorteil 2: Text", max_length=120, blank=True, default="Unkomplizierte Rücksendung",
    )
    benefit_3_title = models.CharField("Vorteil 3: Titel", max_length=60, default="Sichere Zahlung")
    benefit_3_text = models.CharField(
        "Vorteil 3: Text", max_length=120, blank=True, default="Verschlüsselt über Stripe",
    )

    products_title = models.CharField("Produktbereich: Überschrift", max_length=80, default="Beliebte Produkte")
    products_subtitle = models.CharField(
        "Produktbereich: Untertitel", max_length=160, blank=True,
        default="Von unseren Kundinnen und Kunden besonders geschätzt",
    )

    free_shipping_threshold = models.DecimalField(
        "Versandkostenfrei ab (€)", max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Leer lassen, wenn es keinen kostenlosen Versand gibt.",
    )

    shipping_cost = models.DecimalField(
        "Versandkosten (€)", max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Standardversand innerhalb Österreichs. Leer = wird an der Kasse berechnet.",
    )
    delivery_time = models.CharField("Lieferzeit", max_length=60, blank=True, default="2–4 Werktage")
    returns_note = models.CharField(
        "Rückgabe-Hinweis", max_length=120, blank=True, default="14 Tage Widerrufsrecht",
    )
    contact_email = models.EmailField("Kontakt-E-Mail", blank=True)
    contact_phone = models.CharField("Kontakt-Telefon", max_length=40, blank=True)
    hero_image_position = models.CharField(
        "Hero: Bildausschnitt", max_length=10, default="center",
        choices=[("center", "Mitte"), ("left", "Links"), ("right", "Rechts"), ("top", "Oben")],
    )

    class Meta:
        verbose_name = "Shop-Einstellungen"
        verbose_name_plural = "Shop-Einstellungen"

    def __str__(self):
        return "Shop-Einstellungen"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @cached_property
    def brand_css(self):
        """CSS-Variablen für eine eigene Markenfarbe (leer bei Standardfarbe)."""
        return mark_safe(branding.brand_css(self.brand_color))

    @cached_property
    def logo_url(self):
        return self._small_image(self.logo)

    @cached_property
    def logo_dark_url(self):
        return self._small_image(self.logo_dark)

    @cached_property
    def favicon_url(self):
        if not self.favicon:
            return ""
        from shop.images import build_icon
        return build_icon(self.favicon) or self.favicon.url

    @staticmethod
    def _small_image(field_file):
        if not field_file:
            return ""
        from shop.images import build_variant
        return build_variant(field_file, 480) or field_file.url

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def for_request(cls, request):
        if not hasattr(request, "_store_settings"):
            request._store_settings = cls.load()
        return request._store_settings
