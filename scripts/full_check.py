"""Vollständige Prüfung des Shops (läuft gegen die echte Django-Installation).

Crawlt jede Seite, folgt jedem internen Link und testet die Formulare:
Registrieren, Profil, Passwort-Seite, Abmelden, Warenkorb, Kategorien, Suche.

Ausführen im Projektordner (venv aktiv):
    cd /mnt/data/shop-project
    python scripts/full_check.py

Alle Datenbank-Änderungen (Testkonto, Sitzungen) werden am Ende wieder
zurückgerollt – in db.sqlite3 bleibt nichts zurück.
Während des Laufs bitte nicht gleichzeitig im Browser bestellen/anmelden
(SQLite ist für diese Sekunden gesperrt).

Am Ende steht z. B.:
    ERGEBNIS: 180 bestanden, 0 fehlgeschlagen
Die Zahl hängt von der Anzahl der Produkte und Seiten ab.
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

# Django-Test-Client nutzt Host "testserver" – nur für diesen Lauf erlauben.
from django.conf import settings

if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]

from django.db import transaction
from django.test import Client
from django.urls import reverse
from django.utils.html import escape

from pages.models import Page
from shop.context_processors import visible_categories
from shop.models import Product, ProductVariant

PASS, FAIL = [], []

POST_ENDPOINTS = re.compile(r"^/warenkorb/(hinzufuegen|\d+/aktualisieren|\d+/entfernen)/$")
LOGOUT = "/konto/abmelden/"
STATIC = re.compile(r"^/(static|media)/")


def record(ok, label):
    (PASS if ok else FAIL).append(label)


def extract_links(html):
    links = set()
    for m in re.finditer(r'href="(/[^"]*)"', html):
        links.add(m.group(1).split("#")[0] or "/")
    for m in re.finditer(r'action="(/[^"]*)"', html):
        links.add(m.group(1))
    return sorted(link for link in links if link)


def follow(client, name, link):
    """GET für hrefs; POST-only-Endpunkte müssen auf GET mit 405 antworten."""
    if STATIC.match(link):
        return  # static/media liefert runserver aus, nicht der Test-Client
    if POST_ENDPOINTS.match(link) or link == LOGOUT:
        r = client.get(link)
        ok = r.status_code == 405
        print(f"    {'○' if ok else '✗'} {link} -> {r.status_code} auf GET (POST-only erwartet)")
        record(ok, f"{name} -> {link}: {r.status_code} auf GET")
        return
    r = client.get(link)
    ok = r.status_code in (200, 302)
    print(f"    {'✓' if ok else '✗'} {link} -> {r.status_code}")
    record(ok, f"{name} -> {link}: {r.status_code}")


def crawl_page(client, name, path):
    resp = client.get(path)
    print(f"\n### {name}  ({path})  -> {resp.status_code}")
    if resp.status_code != 200:
        FAIL.append(f"{name}: Seite selbst {resp.status_code}")
        return
    links = extract_links(resp.content.decode())
    print(f"    {len(links)} interne Links/Aktionen gefunden")
    for link in links:
        follow(client, name, link)


def check_pages():
    client = Client()
    for p in Product.objects.filter(is_active=True):
        crawl_page(client, f"Produkt {p.slug}", p.get_absolute_url())
    crawl_page(client, "Startseite", "/")
    crawl_page(client, "Warenkorb", "/warenkorb/")
    crawl_page(client, "Suche (leer)", "/suche/")
    for c in visible_categories():
        crawl_page(client, f"Kategorie {c.slug}", c.get_absolute_url())
    crawl_page(client, "Anmelden", "/konto/anmelden/")
    crawl_page(client, "Registrieren", "/konto/registrieren/")
    crawl_page(client, "Passwort vergessen", "/konto/passwort-vergessen/")
    for page in Page.objects.all():
        crawl_page(client, f"Seite {page.slug}", page.get_absolute_url())


def check_account():
    print("\n### KONTO-FLOW")
    client = Client()
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
    ok = r.status_code == 200 and r.request["PATH_INFO"] == reverse("accounts:dashboard")
    print(f"    Registrieren -> {r.status_code}, gelandet auf {r.request['PATH_INFO']}")
    record(ok, "Registrierung")
    if not ok:
        print("    Registrierung fehlgeschlagen – restlicher Konto-Flow übersprungen")
        return

    r = client.get(reverse("accounts:dashboard"))
    html = r.content.decode()
    ok = r.status_code == 200 and "Meine Bestellungen" in html and "Persönliche Daten" in html
    print(f"    Dashboard -> {r.status_code}, Navigation sichtbar: {ok}")
    record(ok, "Dashboard-Inhalt")

    r = client.get(reverse("accounts:profile"))
    ok = r.status_code == 200 and "<form" in r.content.decode()
    print(f"    Persönliche Daten -> {r.status_code}, Formular vorhanden: {ok}")
    record(ok, "Profil-Seite")

    r = client.post(
        reverse("accounts:profile"),
        {"first_name": "Test", "last_name": "Kunde", "phone": "+43 1 234"},
        follow=True,
    )
    print(f"    Profil speichern -> {r.status_code}")
    record(r.status_code == 200, "Profil speichern")

    r = client.get(reverse("accounts:password_change"))
    print(f"    Passwort ändern -> {r.status_code}")
    record(r.status_code == 200, "Passwort-Ändern-Seite")

    r = client.post(reverse("accounts:logout"), follow=True)
    ok = r.status_code == 200
    print(f"    Abmelden -> {r.status_code}, gelandet auf {r.request['PATH_INFO']}")
    record(ok, "Abmelden")

    r = client.get("/")
    ok = "Anmelden" in r.content.decode()
    print(f"    Header zeigt 'Anmelden' nach Abmeldung: {ok}")
    record(ok, "Header-Login-Zustand")


def check_catalog():
    print("\n### KATEGORIEN & SUCHE")
    client = Client()
    categories = list(visible_categories())
    print(f"    {len(categories)} sichtbare Kategorie(n)")
    home = client.get("/").content.decode()
    for c in categories:
        html = client.get(c.get_absolute_url()).content.decode()
        names = [p.name for p in Product.objects.filter(is_active=True, category=c)]
        ok = bool(names) and all(escape(n) in html for n in names)
        print(f"    Kategorie {c.name}: {len(names)} Produkt(e) sichtbar: {ok}")
        record(ok, f"Kategorie {c.slug}: Produkte sichtbar")
        linked = f'href="{c.get_absolute_url()}"' in home
        print(f"    Kategorie {c.name}: auf der Startseite verlinkt: {linked}")
        record(linked, f"Kategorie {c.slug}: Link auf Startseite")

    r = client.get("/kategorie/diese-kategorie-gibt-es-nicht/")
    print(f"    Unbekannte Kategorie -> {r.status_code}")
    record(r.status_code == 404, "Unbekannte Kategorie liefert 404")

    product = Product.objects.filter(is_active=True).first()
    if product is None:
        FAIL.append("Suche: kein aktives Produkt")
        return
    word = max(product.name.split(), key=len)
    html = client.get(reverse("shop:search"), {"q": word}).content.decode()
    ok = escape(product.name) in html and "Ergebnis" in html
    print(f"    Suche nach '{word}': '{product.name}' gefunden: {ok}")
    record(ok, "Suche findet Produkt")

    # SQLite vergleicht nur ASCII-Buchstaben ohne Groß-/Kleinschreibung (PostgreSQL auch Umlaute).
    ascii_words = [w for w in product.name.split() if w.isascii() and len(w) > 2]
    if ascii_words:
        html = client.get(reverse("shop:search"), {"q": ascii_words[0].upper()}).content.decode()
        ok = escape(product.name) in html
        print(f"    Suche nach '{ascii_words[0].upper()}': gefunden: {ok}")
        record(ok, "Suche ignoriert Groß-/Kleinschreibung")

    html = client.get(reverse("shop:search"), {"q": "zzqx-gibt-es-nicht"}).content.decode()
    ok = "Keine Produkte gefunden" in html
    print(f"    Suche ohne Treffer zeigt Hinweis: {ok}")
    record(ok, "Suche ohne Treffer")

    r = client.get(reverse("shop:search"), {"q": '<script>alert(1)</script>"'})
    ok = r.status_code == 200 and "<script>alert(1)" not in r.content.decode()
    print(f"    Suchbegriff wird sicher ausgegeben: {ok}")
    record(ok, "Suche escaped Eingabe")


def check_cart():
    print("\n### WARENKORB-FLOW (über gerenderte Seiten geprüft)")
    client = Client()
    v = ProductVariant.objects.filter(is_active=True, product__is_active=True, stock__gt=0).first()
    if v is None:
        print("    Keine aktive Variante mit Lagerbestand gefunden")
        FAIL.append("Warenkorb: keine lagernde Variante")
        return

    r = client.post(reverse("shop:cart_add"), {"variant": v.id, "quantity": 2, "next": "/"}, follow=True)
    badge = re.search(r'cart-count[^>]*>\s*(\d+)', r.content.decode())
    count_ok = bool(badge) and badge.group(1) == "2"
    print(f"    Hinzufügen x2 -> {r.status_code}, Header-Badge = {badge.group(1) if badge else 'FEHLT'}")
    record(r.status_code == 200 and count_ok, "Warenkorb hinzufügen + Badge")

    html = client.get(reverse("shop:cart")).content.decode()
    qty = re.search(r'name="quantity"[^>]*value="(\d+)"', html)
    ok = v.product.name in html and bool(qty) and qty.group(1) == "2"
    print(f"    Warenkorb-Seite -> Produkt sichtbar: {v.product.name in html}, Menge={qty.group(1) if qty else '?'}")
    record(ok, "Warenkorb-Seiten-Inhalt")

    r = client.post(reverse("shop:cart_update", args=[v.id]), {"quantity": 3, "next": "/warenkorb/"}, follow=True)
    qty = re.search(r'name="quantity"[^>]*value="(\d+)"', r.content.decode())
    ok = bool(qty) and qty.group(1) == "3"
    print(f"    Menge -> 3: gerenderte Menge = {qty.group(1) if qty else '?'}")
    record(ok, "Menge ändern (gerendert)")

    r = client.post(reverse("shop:cart_remove", args=[v.id]), {"next": "/warenkorb/"}, follow=True)
    html = r.content.decode()
    gone = "Ihr Warenkorb ist leer" in html
    print(f"    Entfernen: Warenkorb ist danach leer: {gone}")
    record(gone, "Entfernen (gerendert)")


# Alles in einer Transaktion ausführen und am Ende zurückrollen:
# Testkonto und Sitzungen landen so nicht in der Datenbank.
with transaction.atomic():
    try:
        check_pages()
        check_account()
        check_catalog()
        check_cart()
    finally:
        transaction.set_rollback(True)

print("\n" + "=" * 60)
print(f"ERGEBNIS: {len(PASS)} bestanden, {len(FAIL)} fehlgeschlagen")
print("(Datenbank-Änderungen des Tests wurden zurückgerollt.)")
if FAIL:
    print("\nFEHLGESCHLAGEN:")
    for item in FAIL:
        print(f"  ✗ {item}")
    sys.exit(1)
print("ALLE PRÜFUNGEN BESTANDEN ✓")
