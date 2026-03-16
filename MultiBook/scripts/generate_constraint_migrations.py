"""
Script to add CHECK constraints to all models.

Run this after adding the constraints to Meta classes in models.py files.
This script generates the migration commands.
"""

# ===== ACCOUNTS APP =====
print("=== ACCOUNTS APP ===\n")

print("# User Model")
print("python manage.py makemigrations accounts --name add_user_check_constraints")

print("\n# Invitation Model") 
print("python manage.py makemigrations accounts --name add_invitation_check_constraints")

print("\n# Manager Model (no additional constraints needed)")

print("\n# Profile Model (no additional constraints needed)")

# ===== CUSTOMERS APP =====
print("\n\n=== CUSTOMERS APP ===\n")

print("# Customer Model")
print("python manage.py makemigrations customers --name add_customer_check_constraints")

print("\n# Address Model")
print("python manage.py makemigrations customers --name add_address_check_constraints")

# ===== STAFF APP =====
print("\n\n=== STAFF APP ===\n")

print("# Staff Model")
print("python manage.py makemigrations staff --name add_staff_check_constraints")

print("\n# StaffSchedule Model")
print("python manage.py makemigrations staff --name add_staffschedule_check_constraints")

print("\n# StaffService Model")
print("python manage.py makemigrations staff --name add_staffservice_check_constraints")

print("\n# StaffArea Model")
print("python manage.py makemigrations staff --name add_staffarea_check_constraints")

# ===== SERVICES APP =====
print("\n\n=== SERVICES APP ===\n")

print("# Category Model")
print("python manage.py makemigrations services --name add_category_check_constraints")

print("\n# Service Model")
print("python manage.py makemigrations services --name add_service_check_constraints")

# ===== APPOINTMENTS APP =====
print("\n\n=== APPOINTMENTS APP ===\n")

print("# Appointment Model")
print("python manage.py makemigrations appointments --name add_appointment_check_constraints")

print("\n# CustomerAppointment Model")
print("python manage.py makemigrations appointments --name add_customerappointment_check_constraints")

# ===== ORDERS APP =====
print("\n\n=== ORDERS APP ===\n")

print("# Order Model")
print("python manage.py makemigrations orders --name add_order_check_constraints")

print("\n# OrderItem Model")
print("python manage.py makemigrations orders --name add_orderitem_check_constraints")

print("\n# ChangeRequest Model")
print("python manage.py makemigrations orders --name add_changerequest_check_constraints")

# ===== SUBSCRIPTIONS APP =====
print("\n\n=== SUBSCRIPTIONS APP ===\n")

print("# Subscription Model")
print("python manage.py makemigrations subscriptions --name add_subscription_check_constraints")

print("\n# SubscriptionAppointment Model")
print("python manage.py makemigrations subscriptions --name add_subscriptionappointment_check_constraints")

print("\n# SubscriptionAppointmentChangeRequest Model")
print("python manage.py makemigrations subscriptions --name add_subscriptionappointmentchangerequest_check_constraints")

# ===== COUPONS APP =====
print("\n\n=== COUPONS APP ===\n")

print("# Coupon Model")
print("python manage.py makemigrations coupons --name add_coupon_check_constraints")

print("\n# CouponUsage Model")
print("python manage.py makemigrations coupons --name add_couponusage_check_constraints")

print("\n\n=== ALL MIGRATIONS GENERATED ===")
print("\nTo apply all migrations, run:")
print("python manage.py migrate")
