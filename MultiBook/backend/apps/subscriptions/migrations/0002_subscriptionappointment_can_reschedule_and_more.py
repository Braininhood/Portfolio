# Generated manually for subscription visit change request support

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionappointment',
            name='can_reschedule',
            field=models.BooleanField(
                default=True,
                help_text='Can request change of date/time (based on 24h policy)',
            ),
        ),
        migrations.CreateModel(
            name='SubscriptionAppointmentChangeRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('requested_date', models.DateField(help_text='Requested new date')),
                ('requested_time', models.TimeField(blank=True, help_text='Requested new time', null=True)),
                ('reason', models.TextField(blank=True, help_text='Reason for change', null=True)),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                    default='pending',
                    help_text='Change request status',
                    max_length=20,
                )),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('review_notes', models.TextField(blank=True, null=True)),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_subscription_change_requests',
                    to=settings.AUTH_USER_MODEL,
                    help_text='User who reviewed this request',
                )),
                ('subscription_appointment', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='change_requests',
                    to='subscriptions.subscriptionappointment',
                    help_text='Subscription visit to reschedule',
                )),
            ],
            options={
                'db_table': 'subscriptions_subscriptionappointmentchangerequest',
                'ordering': ['-created_at'],
            },
        ),
    ]
