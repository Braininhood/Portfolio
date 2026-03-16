"""
Backfill CustomerAppointment for order-created appointments.

Use when orders were confirmed before the signal created CustomerAppointment,
so those appointments don't appear on My Bookings (/cus/bookings).
Run: python manage.py backfill_order_customer_appointments
"""
import logging
from django.core.management.base import BaseCommand
from apps.orders.models import Order
from apps.appointments.models import Appointment, CustomerAppointment
from apps.core.utils import can_cancel_or_reschedule

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create CustomerAppointment for order appointments that lack one (so they show on My Bookings).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only report what would be created; do not create.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run – no changes will be made.'))

        created = 0
        skipped_no_customer = 0
        skipped_has_booking = 0
        errors = 0

        orders = Order.objects.filter(
            status='confirmed',
            customer__isnull=False
        ).prefetch_related('items__appointment', 'items__service')

        for order in orders:
            if not order.customer_id:
                skipped_no_customer += 1
                continue
            policy_hours = getattr(order, 'cancellation_policy_hours', 24) or 24
            for item in order.items.all():
                appt = getattr(item, 'appointment', None)
                if not appt:
                    continue
                if CustomerAppointment.objects.filter(appointment=appt, customer=order.customer).exists():
                    skipped_has_booking += 1
                    continue
                if dry_run:
                    self.stdout.write(
                        f'Would create CustomerAppointment: order={order.order_number} appointment_id={appt.id}'
                    )
                    created += 1
                    continue
                try:
                    can_cancel_val, can_reschedule_val, deadline = can_cancel_or_reschedule(
                        appt.start_time, policy_hours
                    )
                    CustomerAppointment.objects.create(
                        customer=order.customer,
                        appointment=appt,
                        number_of_persons=1,
                        total_price=item.total_price,
                        payment_status=order.payment_status or 'pending',
                        cancellation_policy_hours=policy_hours,
                        can_cancel=can_cancel_val,
                        can_reschedule=can_reschedule_val,
                        cancellation_deadline=deadline,
                    )
                    created += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created CustomerAppointment for order {order.order_number} appointment {appt.id}'
                        )
                    )
                except Exception as e:
                    errors += 1
                    logger.exception('Failed to create CustomerAppointment for order %s appointment %s', order.order_number, appt.id)
                    self.stdout.write(
                        self.style.ERROR(f'Error: order {order.order_number} appointment {appt.id}: {e}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. Created={created}, skipped (no customer)={skipped_no_customer}, '
                f'skipped (already has booking)={skipped_has_booking}, errors={errors}'
            )
        )
