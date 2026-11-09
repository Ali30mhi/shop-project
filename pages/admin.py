from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from .models import Page, StoreSettings


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "show_in_footer", "footer_order", "updated_at")
    list_editable = ("show_in_footer", "footer_order")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Hinweisleiste", {"fields": ("announcement",)}),
        ("Versand & Service", {"fields": (
            "shipping_cost", "free_shipping_threshold", "delivery_time", "returns_note",
        )}),
        ("Kontakt", {"fields": ("contact_email", "contact_phone")}),
        ("Startseite: Hero", {"fields": (
            "hero_eyebrow", "hero_title", "hero_text", "hero_button",
            "hero_image", "hero_image_position", "hero_image_alt",
        )}),
        ("Startseite: Produkte", {"fields": ("products_title", "products_subtitle")}),
        ("Startseite: Vorteile", {"fields": (
            ("benefit_1_title", "benefit_1_text"),
            ("benefit_2_title", "benefit_2_text"),
            ("benefit_3_title", "benefit_3_text"),
        )}),
    )

    def has_add_permission(self, request):
        return not StoreSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = StoreSettings.load()
        return redirect(reverse("admin:pages_storesettings_change", args=[obj.pk]))
