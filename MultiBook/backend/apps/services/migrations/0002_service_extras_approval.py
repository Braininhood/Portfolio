# Generated manually - Service extras, approval_status, created_by_staff

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='extras',
            field=models.JSONField(blank=True, default=list, help_text='Optional extras/add-ons: list of {name, price (string or number), description?}'),
        ),
        migrations.AddField(
            model_name='service',
            name='approval_status',
            field=models.CharField(
                choices=[('approved', 'Approved'), ('pending_approval', 'Pending approval')],
                default='approved',
                help_text='Approved = visible to customers; Pending = only after admin/manager approval',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='service',
            name='created_by_staff',
            field=models.ForeignKey(
                blank=True,
                help_text='Staff who created this service (requires approval if set)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='services_created',
                to='staff.staff',
            ),
        ),
    ]
