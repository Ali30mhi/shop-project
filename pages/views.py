from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.html import escape
from django.views.decorators.http import require_GET

from . import branding
from .models import Page, StoreSettings


@require_GET
def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug)
    return render(request, "pages/page.html", {"page": page})


@require_GET
def favicon_svg(request):
    """Standard-Favicon in der Markenfarbe (solange kein eigenes Favicon hochgeladen ist)."""
    store = StoreSettings.for_request(request)
    letter = escape((settings.SITE_NAME or "S").strip()[:1].upper() or "S")
    response = HttpResponse(branding.favicon_svg(store.brand_color, letter), content_type="image/svg+xml")
    response["Cache-Control"] = "public, max-age=86400"
    return response
