from django.urls import path

from . import cart_views, views, wishlist_views

app_name = "shop"

urlpatterns = [
    path("", views.home, name="home"),
    path("produkt/<slug:slug>/", views.product_detail, name="product_detail"),
    path("kategorie/<slug:slug>/", views.category_detail, name="category"),
    path("suche/", views.search, name="search"),
    path("merkliste/", wishlist_views.wishlist_detail, name="wishlist"),
    path("merkliste/umschalten/", wishlist_views.wishlist_toggle, name="wishlist_toggle"),
    path("warenkorb/", cart_views.cart_detail, name="cart"),
    path("warenkorb/hinzufuegen/", cart_views.cart_add, name="cart_add"),
    path("warenkorb/<int:variant_id>/aktualisieren/", cart_views.cart_update, name="cart_update"),
    path("warenkorb/<int:variant_id>/entfernen/", cart_views.cart_remove, name="cart_remove"),
    path("checkout/<int:order_id>/", views.start_checkout, name="start_checkout"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
]