"""
Script to check what data is saved in the database from Week 1.
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import Profile, Manager
from apps.services.models import Category, Service
from apps.staff.models import Staff, StaffSchedule, StaffArea, StaffService
from apps.customers.models import Customer, Address
from apps.appointments.models import Appointment, CustomerAppointment
from apps.orders.models import Order, OrderItem
from apps.subscriptions.models import Subscription, SubscriptionAppointment
# Note: Payments, Notifications, and CalendarSync models may not be fully implemented yet
# from apps.payments.models import Payment
# from apps.notifications.models import Notification
# from apps.calendar_sync.models import CalendarSync

User = get_user_model()

print("=" * 80)
print("WEEK 1 DATABASE INFORMATION CHECK")
print("=" * 80)
print()

# Count all records
print("=== DATABASE TABLES AND RECORD COUNTS ===")
print()
print(f"Users: {User.objects.count()}")
print(f"Profiles: {Profile.objects.count()}")
print(f"Managers: {Manager.objects.count()}")
print(f"Categories: {Category.objects.count()}")
print(f"Services: {Service.objects.count()}")
print(f"Staff: {Staff.objects.count()}")
print(f"Staff Schedules: {StaffSchedule.objects.count()}")
print(f"Staff Areas: {StaffArea.objects.count()}")
print(f"Staff Services: {StaffService.objects.count()}")
print(f"Customers: {Customer.objects.count()}")
print(f"Addresses: {Address.objects.count()}")
print(f"Appointments: {Appointment.objects.count()}")
print(f"Customer Appointments: {CustomerAppointment.objects.count()}")
print(f"Orders: {Order.objects.count()}")
print(f"Order Items: {OrderItem.objects.count()}")
print(f"Subscriptions: {Subscription.objects.count()}")
print(f"Subscription Appointments: {SubscriptionAppointment.objects.count()}")
# print(f"Payments: {Payment.objects.count()}")
# print(f"Notifications: {Notification.objects.count()}")
# print(f"Calendar Syncs: {CalendarSync.objects.count()}")
print()

# User details
print("=== USER DETAILS ===")
if User.objects.exists():
    for u in User.objects.all():
        print(f"  - ID: {u.id}")
        print(f"    Email: {u.email}")
        print(f"    Username: {u.username or 'N/A'}")
        print(f"    Role: {u.role}")
        print(f"    Verified: {u.is_verified}")
        print(f"    Superuser: {u.is_superuser}")
        print(f"    Staff: {u.is_staff}")
        print(f"    Active: {u.is_active}")
        print()
else:
    print("  No users found")
    print()

# Categories and Services
print("=== CATEGORIES ===")
if Category.objects.exists():
    for cat in Category.objects.all():
        print(f"  - {cat.name} (Active: {cat.is_active}, Services: {cat.services.count()})")
        print()
else:
    print("  No categories found")
    print()

print("=== SERVICES ===")
if Service.objects.exists():
    for svc in Service.objects.all():
        print(f"  - {svc.name}")
        print(f"    Category: {svc.category.name}")
        print(f"    Price: £{svc.price}")
        print(f"    Duration: {svc.duration} minutes")
        print(f"    Active: {svc.is_active}")
        print()
else:
    print("  No services found")
    print()

# Staff
print("=== STAFF MEMBERS ===")
if Staff.objects.exists():
    for staff in Staff.objects.all():
        print(f"  - {staff.name}")
        print(f"    Email: {staff.email}")
        print(f"    Phone: {staff.phone or 'N/A'}")
        print(f"    Active: {staff.is_active}")
        print(f"    Services: {staff.services.count()}")
        print(f"    Schedules: {staff.schedules.count()}")
        print(f"    Service Areas: {staff.service_areas.count()}")
        print()
else:
    print("  No staff members found")
    print()

# Customers
print("=== CUSTOMERS ===")
if Customer.objects.exists():
    for cust in Customer.objects.all():
        print(f"  - {cust.name}")
        print(f"    Email: {cust.email}")
        print(f"    Phone: {cust.phone or 'N/A'}")
        print(f"    Postcode: {cust.postcode or 'N/A'}")
        print(f"    User Linked: {'Yes' if cust.user else 'No'}")
        print()
else:
    print("  No customers found")
    print()

# Appointments
print("=== APPOINTMENTS ===")
if Appointment.objects.exists():
    for apt in Appointment.objects.all()[:10]:  # Show first 10
        print(f"  - {apt.service.name} with {apt.staff.name}")
        print(f"    Start: {apt.start_time}")
        print(f"    Status: {apt.status}")
        print(f"    Type: {apt.appointment_type}")
        print()
    if Appointment.objects.count() > 10:
        print(f"  ... and {Appointment.objects.count() - 10} more appointments")
        print()
else:
    print("  No appointments found")
    print()

# Orders
print("=== ORDERS ===")
if Order.objects.exists():
    for order in Order.objects.all()[:5]:  # Show first 5
        print(f"  - Order #{order.order_number}")
        print(f"    Customer: {order.customer.name if order.customer else order.guest_name}")
        print(f"    Status: {order.status}")
        print(f"    Total: £{order.total_amount}")
        print()
    if Order.objects.count() > 5:
        print(f"  ... and {Order.objects.count() - 5} more orders")
        print()
else:
    print("  No orders found")
    print()

# Subscriptions
print("=== SUBSCRIPTIONS ===")
if Subscription.objects.exists():
    for sub in Subscription.objects.all()[:5]:  # Show first 5
        print(f"  - Subscription #{sub.subscription_number}")
        print(f"    Customer: {sub.customer.name if sub.customer else sub.guest_name}")
        print(f"    Service: {sub.service.name}")
        print(f"    Frequency: {sub.frequency}")
        print(f"    Status: {sub.status}")
        print()
    if Subscription.objects.count() > 5:
        print(f"  ... and {Subscription.objects.count() - 5} more subscriptions")
        print()
else:
    print("  No subscriptions found")
    print()

print("=" * 80)
print("DATABASE CHECK COMPLETE")
print("=" * 80)
