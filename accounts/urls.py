from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import LoginForm

app_name = "accounts"

FORM = "accounts/form.html"
MESSAGE = "accounts/message.html"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("registrieren/", views.register, name="register"),
    path("anmelden/", auth_views.LoginView.as_view(
        template_name=FORM,
        redirect_authenticated_user=True,
        authentication_form=LoginForm,
        extra_context={
            "title": "Anmelden",
            "submit_label": "Anmelden",
            "links": [
                (reverse_lazy("accounts:password_reset"), "Passwort vergessen?"),
                (reverse_lazy("accounts:register"), "Noch kein Konto? Jetzt registrieren"),
            ],
        },
    ), name="login"),
    path("abmelden/", auth_views.LogoutView.as_view(), name="logout"),
    path("profil/", views.profile, name="profile"),
    path("bestellungen/<int:order_id>/", views.order_detail, name="order_detail"),
    path("loeschen/", views.delete_account, name="delete"),

    path("passwort-aendern/", auth_views.PasswordChangeView.as_view(
        template_name=FORM,
        success_url=reverse_lazy("accounts:password_change_done"),
        extra_context={
            "title": "Passwort ändern",
            "submit_label": "Passwort ändern",
            "links": [(reverse_lazy("accounts:dashboard"), "Zurück zu Mein Konto")],
        },
    ), name="password_change"),
    path("passwort-aendern/fertig/", auth_views.PasswordChangeDoneView.as_view(
        template_name=MESSAGE,
        extra_context={
            "title": "Passwort geändert",
            "text": "Ihr Passwort wurde erfolgreich geändert.",
            "link_url": reverse_lazy("accounts:dashboard"),
            "link_label": "Zu Mein Konto",
        },
    ), name="password_change_done"),

    path("passwort-vergessen/", auth_views.PasswordResetView.as_view(
        template_name=FORM,
        email_template_name="accounts/email/password_reset.txt",
        subject_template_name="accounts/email/password_reset_subject.txt",
        success_url=reverse_lazy("accounts:password_reset_done"),
        extra_email_context={"site_name": settings.SITE_NAME},
        extra_context={
            "title": "Passwort vergessen",
            "intro": "Geben Sie Ihre E-Mail-Adresse ein. Wir senden Ihnen einen Link, mit dem Sie ein neues Passwort festlegen können.",
            "submit_label": "Link senden",
            "links": [(reverse_lazy("accounts:login"), "Zurück zur Anmeldung")],
        },
    ), name="password_reset"),
    path("passwort-vergessen/gesendet/", auth_views.PasswordResetDoneView.as_view(
        template_name=MESSAGE,
        extra_context={
            "title": "E-Mail gesendet",
            "text": "Falls ein Konto mit dieser E-Mail-Adresse existiert, haben wir Ihnen einen Link gesendet. Bitte prüfen Sie auch Ihren Spam-Ordner.",
        },
    ), name="password_reset_done"),
    path("passwort-neu/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name=FORM,
        success_url=reverse_lazy("accounts:password_reset_complete"),
        extra_context={"title": "Neues Passwort festlegen", "submit_label": "Passwort speichern"},
    ), name="password_reset_confirm"),
    path("passwort-neu/fertig/", auth_views.PasswordResetCompleteView.as_view(
        template_name=MESSAGE,
        extra_context={
            "title": "Passwort gespeichert",
            "text": "Ihr neues Passwort wurde gespeichert. Sie können sich jetzt anmelden.",
            "link_url": reverse_lazy("accounts:login"),
            "link_label": "Anmelden",
        },
    ), name="password_reset_complete"),
]
