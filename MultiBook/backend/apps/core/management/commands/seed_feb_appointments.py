"""
Seed random appointments from 1 Feb 2026 through end of month.
Uses existing staff and services. Run after seed_data (so staff/services exist).
"""
import random
from datetime import date, time, timedelta, datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.services.models import Service
from apps.staff.models import Staff, StaffService
from apps.appointments.models import Appointment


class Command(BaseCommand):
    help = 'Seed random appointments for February 2026 (1st through end of month).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Remove existing appointments in Feb 2026 before seeding',
        )

    def handle(self, *args, **options):
        clear = options['clear']
        start = date(2026, 2, 1)
        end = date(2026, 2, 28)

        if clear:
            start_dt = timezone.make_aware(datetime.combine(start, time.min))
            end_dt = timezone.make_aware(datetime.combine(end, time.max))
            deleted, _ = Appointment.objects.filter(
                start_time__gte=start_dt,
                start_time__lte=end_dt,
            ).delete()
            self.stdout.write(self.style.WARNING(f'Cleared {deleted} appointments in Feb 2026'))

        staff_list = list(Staff.objects.filter(is_active=True).select_related())
        if not staff_list:
            self.stdout.write(self.style.ERROR('No active staff. Run seed_data first.'))
            return

        # Staff -> list of (service, duration) they offer
        staff_services = {}
        for staff in staff_list:
            pairs = list(
                StaffService.objects.filter(staff=staff, is_active=True)
                .select_related('service')
                .values_list('service_id', 'service__duration')
            )
            staff_services[staff.id] = [(sid, dur) for sid, dur in pairs if dur]
        staff_with_services = [s for s in staff_list if staff_services.get(s.id)]
        if not staff_with_services:
            self.stdout.write(self.style.ERROR('No staff with services. Run seed_data first.'))
            return

        slot_minutes = 30
        work_start = time(9, 0)
        work_end = time(17, 0)
        created = 0
        current = start
        while current <= end:
            if current.weekday() >= 5:
                current += timedelta(days=1)
                continue
            # 1–4 appointments per weekday
            per_day = random.randint(1, 4)
            used_starts = set()
            for _ in range(per_day):
                staff = random.choice(staff_with_services)
                services_duration = staff_services.get(staff.id, [])
                if not services_duration:
                    continue
                service_id, duration = random.choice(services_duration)
                try:
                    service = Service.objects.get(id=service_id)
                except Service.DoesNotExist:
                    continue
                start_min = work_start.hour * 60 + work_start.minute
                end_min = work_end.hour * 60 + work_end.minute - duration
                if end_min <= start_min:
                    continue
                slot_count = (end_min - start_min) // slot_minutes
                if slot_count <= 0:
                    continue
                slot_idx = random.randint(0, slot_count - 1) if slot_count > 1 else 0
                minutes_offset = start_min + slot_idx * slot_minutes
                start_time_val = time(minutes_offset // 60, minutes_offset % 60)
                start_dt = timezone.make_aware(datetime.combine(current, start_time_val))
                key = (current, start_time_val)
                if key in used_starts:
                    continue
                used_starts.add(key)
                end_dt = start_dt + timedelta(minutes=duration)
                _, was_created = Appointment.objects.get_or_create(
                    staff=staff,
                    service=service,
                    start_time=start_dt,
                    defaults={
                        'end_time': end_dt,
                        'status': random.choice(['pending', 'confirmed', 'confirmed']),
                    },
                )
                if was_created:
                    created += 1
            current += timedelta(days=1)
        self.stdout.write(self.style.SUCCESS(f'Created {created} appointments for Feb 2026'))