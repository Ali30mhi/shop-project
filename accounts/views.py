from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from shop.models import Order

from .forms import DeleteAccountForm, ProfileForm, RegistrationForm

FORM_TEMPLATE = "accounts/form.html"


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Willkommen! Ihr Kundenkonto wurde erstellt.")
        return redirect("accounts:dashboard")
    return render(request, FORM_TEMPLATE, {
        "form": form,
        "title": "Konto erstellen",
        "submit_label": "Registrieren",
        "show_privacy_note": True,
        "links": [(reverse("accounts:login"), "Bereits registriert? Anmelden")],
    })


@login_required
@require_GET
def dashboard(request):
    orders = request.user.orders.exclude(status=Order.Status.PENDING)
    return render(request, "accounts/dashboard.html", {"orders": orders})


@login_required
@require_GET
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        id=order_id,
        user=request.user,
    )
    return render(request, "accounts/order_detail.html", {"order": order})


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ihre Daten wurden gespeichert.")
        return redirect("accounts:profile")
    return render(request, FORM_TEMPLATE, {
        "form": form,
        "title": "Persönliche Daten",
        "intro": f"Angemeldet als {request.user.email}",
        "submit_label": "Speichern",
        "links": [(reverse("accounts:dashboard"), "Zurück zu Mein Konto")],
    })


@login_required
@require_http_methods(["GET", "POST"])
def delete_account(request):
    if request.user.is_staff:
        messages.error(request, "Administratorkonten können hier nicht gelöscht werden.")
        return redirect("accounts:dashboard")

    form = DeleteAccountForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Ihr Konto wurde gelöscht.")
        return redirect("shop:home")

    return render(request, FORM_TEMPLATE, {
        "form": form,
        "title": "Konto löschen",
        "intro": (
            "Ihr Konto und Ihre persönlichen Daten werden dauerhaft gelöscht. "
            "Bestellungen bleiben aufgrund gesetzlicher Aufbewahrungspflichten "
            "ohne Verknüpfung zu Ihrem Konto gespeichert."
        ),
        "submit_label": "Konto endgültig löschen",
        "danger": True,
        "links": [(reverse("accounts:dashboard"), "Abbrechen")],
    })
