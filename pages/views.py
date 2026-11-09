from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .models import Page


@require_GET
def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug)
    return render(request, "pages/page.html", {"page": page})
