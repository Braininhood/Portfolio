"""
Order Data Verification Script

This script shows:
1. What data is saved to the database after booking completion
2. What information is visible in the admin panel
3. What happens when deleting from admin (cascade behavior)

CORRECT WAYS TO RUN:
1. Django shell (recommended):
   python manage.py shell
   >>> exec(open('verify_order_data.py').read())
   >>> show_order_data()

2. Direct shell command (PowerShell):
   Get-Content verify_order_data.py | python manage.py shell

3. Or copy-paste the show_order_data() function into Django shell
"""
import os
import django

# Setup Django (needed if running as standalone script)
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    django.setup()

# Now safe to import Django models
from apps.orders.models import Order, OrderItem
from apps.customers.models import Customer
from apps.appointments.models import Appointment

def show_order_data():
    """Display what data is saved to the database for an order."""
    print("\n" + "="*80)
    print("ORDER DATA VERIFICATION")
    print("="*80)
    
    # Get the latest order
    latest_order = Order.objects.select_related('customer').prefetch_related('items', 'appointments').order_by('-created_at').first()
    
    if not latest_order:
        print("\n❌ No orders found in database.")
        return
    
    print(f"\n📦 LATEST ORDER: {latest_order.order_number}")
    print("-" * 80)
    
    # 1. ORDER FIELDS SAVED TO DATABASE
    print("\n1️⃣  ORDER FIELDS SAVED TO DATABASE:")
    print("   ─────────────────────────────────────────────────────────────────")
    print(f"   • ID: {latest_order.id}")
    print(f"   • Order Number: {latest_order.order_number}")
    print(f"   • Tracking Token: {latest_order.tracking_token}")
    print(f"   • Is Guest Order: {latest_order.is_guest_order}")
    print(f"   • Account Linked At: {latest_order.account_linked_at or 'Not linked'}")
    
    # Customer info
    if latest_order.customer:
        print(f"   • Customer: {latest_order.customer.name} (ID: {latest_order.customer.id})")
        print(f"     - Email: {latest_order.customer.email}")
        print(f"     - Phone: {latest_order.customer.phone or 'N/A'}")
        print(f"     - Has User Account: {latest_order.customer.user is not None}")
    else:
        print(f"   • Customer: NULL (Guest Order)")
    
    # Guest info
    if latest_order.is_guest_order:
        print(f"   • Guest Email: {latest_order.guest_email}")
        print(f"   • Guest Name: {latest_order.guest_name}")
        print(f"   • Guest Phone: {latest_order.guest_phone}")
    
    # Order status
    print(f"   • Status: {latest_order.status}")
    print(f"   • Payment Status: {latest_order.payment_status}")
    print(f"   • Total Price: £{latest_order.total_price}")
    print(f"   • Deposit Paid: £{latest_order.deposit_paid}")
    
    # Scheduling
    print(f"   • Scheduled Date: {latest_order.scheduled_date}")
    print(f"   • Scheduled Time: {latest_order.scheduled_time}")
    
    # Cancellation
    print(f"   • Cancellation Policy Hours: {latest_order.cancellation_policy_hours}")
    print(f"   • Can Cancel: {latest_order.can_cancel}")
    print(f"   • Can Reschedule: {latest_order.can_reschedule}")
    print(f"   • Cancellation Deadline: {latest_order.cancellation_deadline}")
    
    # Address
    print(f"   • Address Line 1: {latest_order.address_line1}")
    print(f"   • Address Line 2: {latest_order.address_line2 or 'N/A'}")
    print(f"   • City: {latest_order.city}")
    print(f"   • Postcode: {latest_order.postcode}")
    print(f"   • Country: {latest_order.country}")
    
    # Notes
    print(f"   • Notes: {latest_order.notes or 'N/A'}")
    
    # Timestamps
    print(f"   • Created At: {latest_order.created_at}")
    print(f"   • Updated At: {latest_order.updated_at}")
    
    # Order Items
    items = latest_order.items.all()
    print(f"\n   📋 ORDER ITEMS ({items.count()}):")
    for idx, item in enumerate(items, 1):
        print(f"      {idx}. Service: {item.service.name}")
        print(f"         - Staff: {item.staff.name if item.staff else 'Auto-assigned'}")
        print(f"         - Quantity: {item.quantity}")
        print(f"         - Unit Price: £{item.unit_price}")
        print(f"         - Total Price: £{item.total_price}")
        print(f"         - Status: {item.status}")
        if item.appointment:
            print(f"         - Appointment: {item.appointment.id} (Status: {item.appointment.status})")
    
    # Appointments
    appointments = latest_order.appointments.all()
    print(f"\n   📅 APPOINTMENTS ({appointments.count()}):")
    if appointments.exists():
        for idx, apt in enumerate(appointments, 1):
            print(f"      {idx}. ID: {apt.id}")
            print(f"         - Service: {apt.service.name}")
            print(f"         - Staff: {apt.staff.name if apt.staff else 'N/A'}")
            print(f"         - Start Time: {apt.start_time}")
            print(f"         - End Time: {apt.end_time}")
            print(f"         - Status: {apt.status}")
    else:
        print("      (No appointments created yet - will be created when order is confirmed)")
    
    # 2. WHAT'S VISIBLE IN ADMIN PANEL
    print("\n\n2️⃣  WHAT'S VISIBLE IN ADMIN PANEL:")
    print("   ─────────────────────────────────────────────────────────────────")
    print("   List View (Order List):")
    print("   • Order Number")
    print("   • Customer / Guest (custom method showing customer name or guest info)")
    print("   • Total Price")
    print("   • Status")
    print("   • Payment Status")
    print("   • Is Guest Order (checkbox)")
    print("   • Created At")
    
    print("\n   Detail View (Click on Order):")
    print("   📦 Order Information:")
    print("      • Order Number (read-only)")
    print("      • Tracking Token (read-only)")
    print("      • Customer (dropdown - can be changed)")
    print("      • Is Guest Order (checkbox)")
    print("      • Account Linked At (read-only)")
    
    print("\n   👤 Guest Information:")
    print("      • Guest Email")
    print("      • Guest Name")
    print("      • Guest Phone")
    
    print("\n   📊 Order Status:")
    print("      • Status (dropdown: pending, confirmed, in_progress, completed, cancelled)")
    print("      • Payment Status (dropdown: pending, partial, paid, refunded)")
    print("      • Total Price")
    print("      • Deposit Paid")
    
    print("\n   📅 Scheduling:")
    print("      • Scheduled Date")
    print("      • Scheduled Time")
    
    print("\n   ⏰ Cancellation Policy:")
    print("      • Cancellation Policy Hours")
    print("      • Cancellation Deadline (read-only - auto-calculated)")
    print("      • Can Cancel (read-only)")
    print("      • Can Reschedule (read-only)")
    
    print("\n   📍 Service Address:")
    print("      • Address Line 1")
    print("      • Address Line 2")
    print("      • City")
    print("      • Postcode")
    print("      • Country")
    print("      • Notes")
    
    print("\n   🕒 Timestamps:")
    print("      • Created At (read-only)")
    print("      • Updated At (read-only)")
    
    print("\n   📋 Inline Order Items:")
    print("      • Service (autocomplete)")
    print("      • Staff (autocomplete)")
    print("      • Quantity")
    print("      • Unit Price")
    print("      • Total Price")
    print("      • Status")
    
    # 3. DELETE BEHAVIOR
    print("\n\n3️⃣  DELETE BEHAVIOR (What Happens When You Delete from Admin):")
    print("   ─────────────────────────────────────────────────────────────────")
    
    # Check what's related
    order_id = latest_order.id
    items_count = latest_order.items.count()
    appointments_count = latest_order.appointments.count()
    
    print(f"\n   If you delete Order #{order_id} ({latest_order.order_number}):")
    print(f"   ┌────────────────────────────────────────────────────────────┐")
    print(f"   │ DELETED:                                                   │")
    print(f"   │ • Order record itself                                      │")
    print(f"   │ • {items_count} OrderItem(s) (cascade delete)               │")
    
    if appointments_count > 0:
        print(f"   │                                                              │")
        print(f"   │ RELATED (Check Foreign Keys):                              │")
        print(f"   │ • {appointments_count} Appointment(s) - CHECK FK BEHAVIOR   │")
        print(f"   │   - If Appointment.order_id has on_delete=SET_NULL:         │")
        print(f"   │     → Appointments remain, order_id set to NULL             │")
        print(f"   │   - If Appointment.order_id has on_delete=CASCADE:          │")
        print(f"   │     → Appointments deleted                                  │")
    
    print(f"   │                                                              │")
    print(f"   │ NOT DELETED:                                                │")
    print(f"   │ • Customer record (if exists) - Order.customer FK uses      │")
    print(f"   │   on_delete=SET_NULL, so customer stays                     │")
    
    if latest_order.customer:
        print(f"   │ • Customer #{latest_order.customer.id} ({latest_order.customer.name})  │")
        print(f"   │   will remain in database                                │")
    
    print(f"   │ • Service records (OrderItem.service FK)                    │")
    print(f"   │ • Staff records (OrderItem.staff FK)                        │")
    print(f"   └────────────────────────────────────────────────────────────┘")
    
    # Check Appointment model for FK behavior
    try:
        from apps.appointments.models import Appointment
        from django.db.models import CASCADE, SET_NULL, PROTECT, DO_NOTHING
        order_fk = Appointment._meta.get_field('order')
        on_delete = order_fk.remote_field.on_delete
        
        # Determine on_delete type by checking against Django constants
        on_delete_str = None
        if on_delete == CASCADE:
            on_delete_str = 'CASCADE'
        elif on_delete == SET_NULL:
            on_delete_str = 'SET_NULL'
        elif on_delete == PROTECT:
            on_delete_str = 'PROTECT'
        elif on_delete == DO_NOTHING:
            on_delete_str = 'DO_NOTHING'
        else:
            # Fallback: try to get from function name
            on_delete_str = on_delete.__name__ if hasattr(on_delete, '__name__') else str(type(on_delete).__name__)
        
        print(f"\n   🔍 ACTUAL FK BEHAVIOR:")
        print(f"      Appointment.order on_delete: {on_delete_str}")
        if on_delete_str == 'CASCADE':
            print(f"      → Appointments WILL BE DELETED with order")
        elif on_delete_str == 'SET_NULL':
            print(f"      → Appointments will remain, order_id set to NULL")
        elif on_delete_str == 'PROTECT':
            print(f"      → Cannot delete order if appointments exist")
    except Exception as e:
        print(f"\n   ⚠️  Could not check Appointment FK: {e}")
    
    print("\n" + "="*80)
    print("✅ VERIFICATION COMPLETE")
    print("="*80 + "\n")

# Run the function if script is executed directly
if __name__ == '__main__':
    show_order_data()

# Also allow calling from Django shell
# In Django shell: >>> exec(open('verify_order_data.py').read()); show_order_data()
