# Generated manually for job completion photos (Supabase Storage)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='completion_photos',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Job completion photos in Supabase Storage: list of {url, path, uploaded_at}',
            ),
        ),
    ]
