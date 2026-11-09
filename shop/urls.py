from django.urls import path
from . import views

urlpatterns = [
    path("checkout/<int:order_id>/", views.start_checkout, name="start_checkout"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
]
