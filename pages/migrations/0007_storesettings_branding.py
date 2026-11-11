import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0006_storesettings_contact_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='storesettings',
            name='brand_color',
            field=models.CharField(default='#db3012', help_text='Farbe für Buttons, Links und Akzente. Schriftfarbe und dunkles Design werden automatisch passend berechnet. Standard: #db3012 (Orange).', max_length=7, validators=[django.core.validators.RegexValidator('^#[0-9a-fA-F]{6}$', 'Bitte eine Farbe im Format #rrggbb angeben.')], verbose_name='Markenfarbe'),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='favicon',
            field=models.ImageField(blank=True, help_text='Quadratisches PNG, mindestens 180 × 180 px. Leer = farbiges Quadrat mit dem ersten Buchstaben des Shopnamens.', upload_to='site/', verbose_name='Favicon (Symbol im Browser-Tab)'),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='logo',
            field=models.ImageField(blank=True, help_text='PNG oder WebP mit transparentem Hintergrund, Querformat, mindestens 80 px hoch. Leer = Buchstaben-Logo mit dem Shopnamen.', upload_to='site/', verbose_name='Logo'),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='logo_dark',
            field=models.ImageField(blank=True, help_text='Optional: helle Variante für das dunkle Design und den Footer. Leer = das Logo wird dort auf einer weißen Fläche gezeigt.', upload_to='site/', verbose_name='Logo für dunklen Hintergrund'),
        ),
    ]
