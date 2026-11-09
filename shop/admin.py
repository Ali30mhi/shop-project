from django.contrib import admin

from .models import Order, OrderItem, Product, ProductImage, ProductVariant


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = (
        "color_name", "color_hex", "size", "name", "sku",
        "price", "compare_at_price", "stock", "is_active", "sort_order",
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "sort_order")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline, ProductImageInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "is_active")}),
        ("Inhalt", {"fields": ("short_description", "description", "size_guide")}),
        ("Suchmaschinen (SEO)", {"fields": ("meta_title", "meta_description")}),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ("product_name", "variant_name", "sku", "unit_price", "quantity")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "total", "currency", "status", "created_at", "paid_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "email", "full_name", "invoice_number")
    readonly_fields = (
        "user",
        "stripe_session_id",
        "stripe_invoice_id",
        "invoice_number",
        "invoice_url",
        "invoice_pdf_url",
        "created_at",
        "paid_at",
    )
    inlines = [OrderItemInline]
