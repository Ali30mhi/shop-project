from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Kundenkonten"

    def ready(self):
        from django.contrib import messages
        from django.contrib.auth.signals import user_logged_out

        def show_logout_message(sender, request, user, **kwargs):
            if request is not None and not request.path.startswith("/admin/"):
                messages.info(request, "Sie wurden erfolgreich abgemeldet.")

        user_logged_out.connect(show_logout_message, dispatch_uid="accounts_logout_message")
