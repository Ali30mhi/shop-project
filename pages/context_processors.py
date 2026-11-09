from .models import Page, StoreSettings


def site_content(request):
    return {
        "footer_pages": Page.objects.filter(show_in_footer=True).only("title", "slug"),
        "store": StoreSettings.load(),
    }
