"""
Quick script to view order data saved in database.

Usage:
    python manage.py shell
    >>> exec(open('view_order_data.py').read())
"""

from apps.orders.models import Order, OrderItem
from apps.customers.models import Customer
from apps.appointments.models import Appointment

# Get latest order
latest_order = Order.objects.select_related('customer').prefetch_related('items', 'appointments').order_by('-created_at').first()

if not latest_order:
    print("❌ No orders found in database.")
else:
    print(f"\n📦 LATEST ORDER: {latest_order.order_number}")
    print("="*80)
    
    # Show all saved fields
    print("\n✅ SAVED DATA:")
    print(f"   Order Number: {latest_order.order_number}")
    print(f"   Tracking Token: {latest_order.tracking_token}")
    print(f"   Is Guest Order: {latest_order.is_guest_order}")
    print(f"   Status: {latest_order.status}")
    print(f"   Payment Status: {latest_order.payment_status}")
    print(f"   Total Price: £{latest_order.total_price}")
    
    if latest_order.customer:
        print(f"\n   👤 CUSTOMER:")
        print(f"      ID: {latest_order.customer.id}")
        print(f"      Name: {latest_order.customer.name}")
        print(f"      Email: {latest_order.customer.email}")
        print(f"      Phone: {latest_order.customer.phone or 'N/A'}")
        print(f"      Has User Account: {latest_order.customer.user is not None}")
    else:
        print(f"\n   👤 GUEST ORDER:")
        print(f"      Email: {latest_order.guest_email}")
        print(f"      Name: {latest_order.guest_name}")
        print(f"      Phone: {latest_order.guest_phone or 'N/A'}")
    
    print(f"\n   📅 SCHEDULING:")
    print(f"      Date: {latest_order.scheduled_date}")
    print(f"      Time: {latest_order.scheduled_time}")
    
    print(f"\n   📍 ADDRESS:")
    print(f"      {latest_order.address_line1}")
    if latest_order.address_line2:
        print(f"      {latest_order.address_line2}")
    print(f"      {latest_order.city}, {latest_order.postcode}")
    print(f"      {latest_order.country}")
    
    print(f"\n   📋 ORDER ITEMS ({latest_order.items.count()}):")
    for item in latest_order.items.all():
        print(f"      • {item.service.name} x{item.quantity}")
        print(f"        Staff: {item.staff.name if item.staff else 'Auto-assigned'}")
        print(f"        Price: £{item.unit_price} × {item.quantity} = £{item.total_price}")
    
    print(f"\n   📅 APPOINTMENTS ({latest_order.appointments.count()}):")
    if latest_order.appointments.exists():
        for apt in latest_order.appointments.all():
            print(f"      • Appointment #{apt.id}")
            print(f"        Service: {apt.service.name}")
            print(f"        Staff: {apt.staff.name if apt.staff else 'N/A'}")
            print(f"        Time: {apt.start_time} - {apt.end_time}")
    else:
        print("      (No appointments created yet)")
    
    print(f"\n   🕒 TIMESTAMPS:")
    print(f"      Created: {latest_order.created_at}")
    print(f"      Updated: {latest_order.updated_at}")
    if latest_order.account_linked_at:
        print(f"      Linked: {latest_order.account_linked_at}")
    
    print("\n" + "="*80)
