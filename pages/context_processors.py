from .models import Page


def footer_pages(request):
    return {"footer_pages": Page.objects.filter(show_in_footer=True).only("title", "slug")}
