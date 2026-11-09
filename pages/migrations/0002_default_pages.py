from django.db import migrations

DEFAULT_PAGES = [
    ("Impressum", "impressum", 10),
    ("Datenschutzerklärung", "datenschutz", 20),
    ("AGB", "agb", 30),
    ("Widerrufsrecht", "widerrufsrecht", 40),
    ("Versand & Zahlung", "versand-und-zahlung", 50),
]


def create_pages(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    for title, slug, order in DEFAULT_PAGES:
        Page.objects.get_or_create(slug=slug, defaults={"title": title, "footer_order": order})


def remove_pages(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    Page.objects.filter(slug__in=[slug for _, slug, _ in DEFAULT_PAGES]).delete()


class Migration(migrations.Migration):
    dependencies = [("pages", "0001_initial")]
    operations = [migrations.RunPython(create_pages, remove_pages)]
