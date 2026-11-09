from django.db import models
from django.urls import reverse
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe


class Page(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    body = models.TextField(
        blank=True,
        help_text="Text oder HTML. Rechtstexte aus einem Generator können direkt eingefügt werden.",
    )
    meta_description = models.CharField(max_length=160, blank=True)
    show_in_footer = models.BooleanField(default=True)
    footer_order = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["footer_order", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("pages:detail", args=[self.slug])

    @property
    def rendered_body(self):
        if "<" in self.body:
            return mark_safe(self.body)
        return mark_safe(linebreaks(self.body, autoescape=True))
