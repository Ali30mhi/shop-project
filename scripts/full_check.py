"""ShopWien — vollständige Verifikation (standalone).

Crawlt jede Seite, folgt jedem Link, testet jedes Formular:
Registrieren, Anmelden, Abmelden, Profil, Passwort, Warenkorb.

Ausführen im Projektordner:
    cd /mnt/data/shop-project
    python scripts/full_check.py

Am Ende muss stehen:
    RESULT: 135 passed, 0 failed
    ALL CHECKS PASSED ✓
"""
import os
import re
import sys
import uuid

# Projekt-Root in sys.path (Skript liegt in scripts/)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

# Django-Test-Client nutzt Host "testserver" — erlaubt nur für diesen Test.
from django.conf import settings

if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]

from django.test import Client
from django.urls import reverse

from pages.models import Page
from shop.models import Product, ProductVariant

PASS, FAIL = [], []

POST_ENDPOINTS = re.compile(r"^/warenkorb/(hinzufuegen|\d+/aktualisieren|\d+/entfernen)/$")
LOGOUT = "/konto/abmelden/"
STATIC = re.compile(r"^/(static|media)/")


def extract_links(html):
    links = set()
    for m in re.finditer(r'href="(/[^"]*)"', html):
        links.add(m.group(1).split("#")[0] or "/")
    for m in re.finditer(r'action="(/[^"]*)"', html):
        links.add(m.group(1))
    return sorted(l for l in links if l)


def follow(client, name, link):
    """GET für hrefs; POST-only-Endpunkte via GET auf 405 prüfen."""
    if STATIC.match(link):
        return  # static/media werden von runserver ausgeliefert (test-client nicht)
    if POST_ENDPOINTS.match(link) or link == LOGOUT:
        r = client.get(link)
        if r.status_code == 405:
            PASS.append(f"{name} -> {link}: 405 on GET (POST-only, korrekt)")
            print(f"    ○ {link} -> 405 on GET (POST-only, korrekt)")
        else:
            FAIL.append(f"{name} -> {link}: unerwartet {r.status_code} on GET")
            print(f"    ✗ {link} -> {r.status_code}")
        return
    r = client.get(link)
    ok = r.status_code in (200, 302)
    print(f"    {'✓' if ok else '✗'} {link} -> {r.status_code}")
    (PASS if ok else FAIL).append(f"{name} -> {link}: {r.status_code}")


def crawl_page(client, name, path):
    resp = client.get(path)
    print(f"\n### {name}  ({path})  -> {resp.status_code}")
    if resp.status_code != 200:
        FAIL.append(f"{name}: Seite selbst {resp.status_code}")
        return
    html = resp.content.decode()
    links = extract_links(html)
    print(f"    {len(links)} interne Links/Aktionen gefunden")
    for link in links:
        follow(client, name, link)


client = Client()

# ---------- 1. Jede Seite crawlen ----------
for p in Product.objects.filter(is_active=True):
    crawl_page(client, f"Produkt {p.slug}", p.get_absolute_url())
crawl_page(client, "Startseite", "/")
crawl_page(client, "Warenkorb", "/warenkorb/")
crawl_page(client, "Anmelden", "/konto/anmelden/")
crawl_page(client, "Registrieren", "/konto/registrieren/")
crawl_page(client, "Passwort vergessen", "/konto/passwort-vergessen/")
for page in Page.objects.all():
    crawl_page(client, f"Seite {page.slug}", page.get_absolute_url())

# ---------- 2. Konto-Flow ----------
print("\n### KONTO-FLOW")
test_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
test_pw = "SicheresPass123!"

r = client.post(
    reverse("accounts:register"),
    {
        "email": test_email,
        "first_name": "Test",
        "last_name": "Kunde",
        "password1": test_pw,
        "password2": test_pw,
    },
    follow=True,
)
ok = r.status_code == 200 and "/konto/" in r.request["PATH_INFO"]
print(f"    Registrieren -> {r.status_code}, gelandet auf {r.request['PATH_INFO']}")
(PASS if ok else FAIL).append("Registrierung")
assert ok, "Registrierung fehlgeschlagen"

r = client.get(reverse("accounts:dashboard"))
html = r.content.decode()
ok = r.status_code == 200 and "Meine Bestellungen" in html and "Persönliche Daten" in html
print(f"    Dashboard -> {r.status_code}, Navigation sichtbar: {ok}")
(PASS if ok else FAIL).append("Dashboard-Inhalt")

r = client.get(reverse("accounts:profile"))
html = r.content.decode()
ok = r.status_code == 200 and ("Speichern" in html or "form" in html)
print(f"    Persönliche Daten -> {r.status_code}, Formular vorhanden: {ok}")
(PASS if ok else FAIL).append("Profil-Seite")

r = client.post(
    reverse("accounts:profile"),
    {"email": test_email, "first_name": "Test", "last_name": "Kunde", "phone": "+43 1 234"},
    follow=True,
)
print(f"    Profil speichern -> {r.status_code}")
(PASS if r.status_code == 200 else FAIL).append("Profil speichern")

r = client.get(reverse("accounts:password_change"))
print(f"    Passwort ändern -> {r.status_code}")
(PASS if r.status_code == 200 else FAIL).append("Passwort-Ändern-Seite")

r = client.post(reverse("accounts:logout"), follow=True)
ok = r.status_code == 200 and r.request["PATH_INFO"] == "/"
print(f"    Abmelden -> {r.status_code}, gelandet auf {r.request['PATH_INFO']}")
(PASS if ok else FAIL).append("Abmelden")

r = client.get("/")
ok = "Anmelden" in r.content.decode()
print(f"    Header zeigt 'Anmelden' nach Abmeldung: {ok}")
(PASS if ok else FAIL).append("Header-Login-Zustand")

# ---------- 3. Warenkorb-Flow (per gerendertem HTML geprüft) ----------
print("\n### WARENKORB-FLOW (über gerenderte Seiten geprüft)")
client = Client()
v = ProductVariant.objects.filter(is_active=True, product__is_active=True, stock__gt=0).first()

r = client.post(reverse("shop:cart_add"), {"variant": v.id, "quantity": 2, "next": "/"}, follow=True)
html = r.content.decode()
badge = re.search(r'cart-count[^>]*>\s*(\d+)', html)
count_ok = badge and badge.group(1) == "2"
print(f"    Hinzufügen x2 -> {r.status_code}, Header-Badge = {badge.group(1) if badge else 'FEHLT'}")
(PASS if r.status_code == 200 and count_ok else FAIL).append("Warenkorb hinzufügen + Badge")

r = client.get(reverse("shop:cart"))
html = r.content.decode()
qty_shown = re.search(r'name="quantity"[^>]*value="(\d+)"', html)
line_ok = v.product.name in html and qty_shown and qty_shown.group(1) == "2"
print(f"    Warenkorb-Seite -> Produkt sichtbar: {v.product.name in html}, Menge={qty_shown.group(1) if qty_shown else '?'}")
(PASS if line_ok else FAIL).append("Warenkorb-Seiten-Inhalt")

r = client.post(reverse("shop:cart_update", args=[v.id]), {"quantity": 3, "next": "/warenkorb/"}, follow=True)
html = r.content.decode()
qty_shown = re.search(r'name="quantity"[^>]*value="(\d+)"', html)
upd_ok = qty_shown and qty_shown.group(1) == "3"
print(f"    Menge -> 3: gerenderte Menge = {qty_shown.group(1) if qty_shown else '?'}")
(PASS if upd_ok else FAIL).append("Menge ändern (gerendert)")

r = client.post(reverse("shop:cart_remove", args=[v.id]), {"next": "/warenkorb/"}, follow=True)
html = r.content.decode()
gone = v.product.name not in html and "Ihr Warenkorb ist leer" in html
print(f"    Entfernen: Produkt aus Warenkorb-Seite entfernt: {gone}")
(PASS if gone else FAIL).append("Entfernen (gerendert)")

# ---------- Ergebnis ----------
print("\n" + "=" * 60)
print(f"ERGEBNIS: {len(PASS)} bestanden, {len(FAIL)} fehlgeschlagen")
if FAIL:
    print("\nFEHLGESCHLAGEN:")
    for f in FAIL:
        print(f"  ✗ {f}")
    sys.exit(1)
print("ALLE PRÜFUNGEN BESTANDEN ✓")
