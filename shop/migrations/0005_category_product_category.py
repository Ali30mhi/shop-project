import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_product_size_guide'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('slug', models.SlugField(blank=True, help_text='Wird automatisch aus dem Namen erzeugt.', max_length=120, unique=True, verbose_name='URL-Kürzel')),
                ('description', models.CharField(blank=True, help_text='Erscheint auf der Kategorie-Kachel und auf der Kategorieseite.', max_length=200, verbose_name='Kurzbeschreibung')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Reihenfolge')),
                ('is_active', models.BooleanField(default=True, help_text='Kategorien ohne aktive Produkte werden im Shop nicht angezeigt.', verbose_name='Aktiv')),
            ],
            options={
                'verbose_name': 'Kategorie',
                'verbose_name_plural': 'Kategorien',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='shop.category', verbose_name='Kategorie'),
        ),
    ]
