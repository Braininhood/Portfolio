# Generated manually - StaffArea per-service (optional service FK)

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0002_convert_radius_to_miles'),
        ('services', '0002_service_extras_approval'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffarea',
            name='service',
            field=models.ForeignKey(
                blank=True,
                help_text='If set, this area applies only to this service; null = all services',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='staff_areas',
                to='services.service',
            ),
        ),
    ]
