from django.db import models
from django.urls import reverse
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe


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
    hero_button = models.CharField("Hero: Button-Text", max_length=40, default="Produkte ansehen")
    hero_image = models.ImageField(
        "Hero: Bild", upload_to="site/", blank=True, help_text="Querformat, mindestens 1800 px breit.",
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

    class Meta:
        verbose_name = "Shop-Einstellungen"
        verbose_name_plural = "Shop-Einstellungen"

    def __str__(self):
        return "Shop-Einstellungen"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
