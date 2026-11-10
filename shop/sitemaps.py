from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .context_processors import visible_categories
from .models import Product


class BaseSitemap(Sitemap):
    protocol = None if settings.DEBUG else "https"


class StaticSitemap(BaseSitemap):
    changefreq = "weekly"
    priority = 1.0

    def items(self):
        return ["shop:home"]

    def location(self, item):
        return reverse(item)


class CategorySitemap(BaseSitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return visible_categories()


class ProductSitemap(BaseSitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at