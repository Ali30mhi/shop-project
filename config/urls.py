from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from pages.views import favicon_svg
from shop.sitemaps import CategorySitemap, ProductSitemap, StaticSitemap
from shop.views import robots_txt

sitemaps = {
    "static": StaticSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("favicon.svg", favicon_svg, name="favicon_svg"),
    path("konto/", include("accounts.urls")),
    path("", include("shop.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path("", include("pages.urls")),
]
