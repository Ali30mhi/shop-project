import os
import re
import shutil
from pathlib import Path

from django.conf import settings
from django.test import Client

from pages.models import Page
from shop.models import Product, ProductVariant

PREFIX = os.environ.get("PREVIEW_PREFIX", "/shop-vorschau")
OUT = Path(settings.BASE_DIR).parent / os.environ.get("PREVIEW_DIR", "shop-preview")
PALETTE = os.environ.get("PREVIEW_PALETTE", "")
LABEL = os.environ.get("PREVIEW_LABEL", "")
PREVIEW_URL = "https://ali30mhi.github.io" + PREFIX

palette_css = Path(settings.BASE_DIR, PALETTE).read_text() if PALETTE else ""

BANNER = (
    '<div style="background:#fff3cd;color:#5c4400;text-align:center;padding:8px 16px;'
    'font:600 13px/1.4 system-ui,sans-serif;">Vorschau' + (f" – {LABEL}" if LABEL else "") +
    ' – Warenkorb, Login und Bestellung sind in dieser Demo deaktiviert.</div>'
)
BLOCK_POST = (
    "<script>document.addEventListener('submit',function(e){"
    "if((e.target.method||'').toLowerCase()==='post'){e.preventDefault();"
    "alert('Vorschau: Diese Funktion ist in der Demo deaktiviert.');}},true);</script>"
)

OUT.mkdir(exist_ok=True)
for item in OUT.iterdir():
    if item.name == ".git":
        continue
    if item.is_dir():
        shutil.rmtree(item)
    else:
        item.unlink()

settings.SITE_URL = PREVIEW_URL
settings.SEO_NOINDEX = True
settings.SITE_THEME = os.environ.get("PREVIEW_THEME", getattr(settings, "SITE_THEME", "classic"))
client = Client(HTTP_HOST="localhost")

for sku in ("SAD-COG", "VASE-SAL"):
    variant = ProductVariant.objects.filter(sku=sku, is_active=True, stock__gt=0).first()
    if variant:
        client.post("/warenkorb/hinzufuegen/", {"variant": variant.id, "quantity": 1})


def prefix_urls(html):
    html = re.sub(r'(\s(?:href|src|action)=")/(?!/)', lambda m: m.group(1) + PREFIX + "/", html)

    def fix_srcset(match):
        candidates = []
        for candidate in match.group(2).split(","):
            candidate = candidate.strip()
            if candidate.startswith("/") and not candidate.startswith("//"):
                candidate = PREFIX + candidate
            candidates.append(candidate)
        return match.group(1) + ", ".join(candidates) + '"'

    return re.sub(r'(\ssrcset=")([^"]*)"', fix_srcset, html)


def write_page(html, target):
    html = prefix_urls(html)
    if palette_css:
        html = html.replace("</head>", "<style>" + palette_css + "</style></head>", 1)
    html = re.sub(r"<body[^>]*>", lambda m: m.group(0) + BANNER, html, count=1)
    html = html.replace("</body>", BLOCK_POST + "</body>", 1)
    path = OUT / target
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


urls = ["/", "/warenkorb/", "/konto/anmelden/", "/konto/registrieren/", "/konto/passwort-vergessen/"]
urls += [p.get_absolute_url() for p in Product.objects.filter(is_active=True)]
urls += [p.get_absolute_url() for p in Page.objects.all()]

for url in urls:
    response = client.get(url)
    if response.status_code != 200:
        print("WARNUNG:", url, response.status_code)
        continue
    target = "index.html" if url == "/" else url.strip("/") + "/index.html"
    write_page(response.content.decode("utf-8"), target)
    print("OK:", url)

settings.DEBUG = False
response = client.get("/diese-seite-gibt-es-nicht/")
write_page(response.content.decode("utf-8"), "404.html")
settings.DEBUG = True
print("OK: 404.html")

shutil.copytree(Path(settings.BASE_DIR) / "static", OUT / "static")
shutil.copytree(Path(settings.MEDIA_ROOT), OUT / "media")
(OUT / ".nojekyll").write_text("")
print("Fertig:", OUT)
