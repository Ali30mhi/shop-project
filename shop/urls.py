from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("", views.home, name="home"),
    path("produkt/<slug:slug>/", views.product_detail, name="product_detail"),
    path("checkout/<int:order_id>/", views.start_checkout, name="start_checkout"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
]