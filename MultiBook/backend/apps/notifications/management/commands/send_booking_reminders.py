"""
Send booking reminder emails for appointments happening in ~24 hours.
Run daily via cron or Supabase pg_cron / Edge Function.
Example: python manage.py send_booking_reminders --settings=config.settings.development
"""
import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send reminder emails for appointments scheduled in the next 23–25 hours (run daily, e.g. via cron or Supabase pg_cron).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only list appointments that would get a reminder; do not send.',
        )
        parser.add_argument(
            '--hours-min',
            type=int,
            default=23,
            help='Send reminder if appointment is at least this many hours from now (default: 23).',
        )
        parser.add_argument(
            '--hours-max',
            type=int,
            default=25,
            help='Send reminder if appointment is at most this many hours from now (default: 25).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        hours_min = options['hours_min']
        hours_max = options['hours_max']

        from apps.appointments.models import Appointment
        from apps.notifications.email_service import send_booking_reminder

        now = timezone.now()
        window_start = now + timedelta(hours=hours_min)
        window_end = now + timedelta(hours=hours_max)

        # Appointments with start_time in [window_start, window_end], not cancelled
        appointments = Appointment.objects.filter(
            start_time__gte=window_start,
            start_time__lte=window_end,
            status__in=['confirmed', 'pending'],
        ).select_related('order', 'service', 'staff')

        count = 0
        for appointment in appointments:
            if dry_run:
                self.stdout.write(
                    f'[DRY-RUN] Would send reminder: appointment {appointment.id} '
                    f'({appointment.service.name}) at {appointment.start_time}'
                )
                count += 1
                continue
            try:
                if send_booking_reminder(appointment):
                    count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Sent reminder for appointment {appointment.id} ({appointment.service.name}) at {appointment.start_time}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Could not send reminder for appointment {appointment.id} (no recipient or send failed)'
                        )
                    )
            except Exception as e:
                logger.exception(f"Error sending reminder for appointment {appointment.id}")
                self.stdout.write(self.style.ERROR(f'Error: {e}'))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'[DRY-RUN] Would send {count} reminder(s).'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Sent {count} reminder(s).'))
