import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0005_category_product_category'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WishlistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Gemerkt am')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlist_items', to='shop.product', verbose_name='Produkt')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlist_items', to=settings.AUTH_USER_MODEL, verbose_name='Kundenkonto')),
            ],
            options={
                'verbose_name': 'Merklisten-Eintrag',
                'verbose_name_plural': 'Merkliste',
                'ordering': ['-created_at'],
                'constraints': [models.UniqueConstraint(fields=('user', 'product'), name='unique_wishlist_item')],
            },
        ),
    ]
