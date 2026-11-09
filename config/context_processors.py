from django.conf import settings


def site(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_DESCRIPTION": settings.SITE_DESCRIPTION,
        "SITE_URL": settings.SITE_URL.rstrip("/"),
        "SEO_NOINDEX": settings.SEO_NOINDEX,
        "SHOP_TAX_NOTE": settings.SHOP_TAX_NOTE,
    }