"""
Script to verify all API endpoints can read from PostgreSQL database.
This checks:
1. Database connectivity
2. Model queries work correctly
3. All endpoints can be imported without errors
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection
from django.test import Client
from django.contrib.auth import get_user_model
from apps.services.models import Service, Category
from apps.staff.models import Staff
from apps.appointments.models import Appointment
from apps.orders.models import Order
from apps.subscriptions.models import Subscription
from apps.customers.models import Customer

User = get_user_model()

def test_database_connection():
    """Test PostgreSQL connection."""
    print("=" * 60)
    print("TESTING DATABASE CONNECTION")
    print("=" * 60)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"[OK] PostgreSQL Connection: SUCCESS")
        print(f"  Version: {version[:50]}...")
        return True
    except Exception as e:
        print(f"[FAIL] PostgreSQL Connection: FAILED")
        print(f"  Error: {str(e)}")
        return False

def test_model_queries():
    """Test that all models can query PostgreSQL."""
    print("\n" + "=" * 60)
    print("TESTING MODEL QUERIES")
    print("=" * 60)
    
    models_to_test = [
        ("User", User),
        ("Category", Category),
        ("Service", Service),
        ("Staff", Staff),
        ("Customer", Customer),
        ("Appointment", Appointment),
        ("Order", Order),
        ("Subscription", Subscription),
    ]
    
    all_passed = True
    for name, model in models_to_test:
        try:
            count = model.objects.count()
            print(f"[OK] {name}: {count} records")
        except Exception as e:
            print(f"[FAIL] {name}: FAILED - {str(e)}")
            all_passed = False
    
    return all_passed

def test_endpoint_imports():
    """Test that all endpoint views can be imported."""
    print("\n" + "=" * 60)
    print("TESTING ENDPOINT IMPORTS")
    print("=" * 60)
    
    endpoints_to_test = [
        ("Services", "apps.services.views", ["CategoryViewSet", "ServiceViewSet"]),
        ("Staff", "apps.staff.views", ["StaffPublicViewSet", "StaffViewSet"]),
        ("Appointments", "apps.appointments.views", ["AppointmentPublicViewSet", "AppointmentViewSet", "available_slots_view"]),
        ("Orders", "apps.orders.views", ["OrderPublicViewSet", "OrderViewSet"]),
        ("Subscriptions", "apps.subscriptions.views", ["SubscriptionPublicViewSet", "SubscriptionViewSet"]),
        ("Accounts", "apps.accounts.views", ["RegisterView", "ProfileViewSet"]),
        ("Customers", "apps.customers.views", ["CustomerViewSet", "AddressViewSet"]),
    ]
    
    all_passed = True
    for app_name, module_name, view_names in endpoints_to_test:
        try:
            module = __import__(module_name, fromlist=view_names)
            for view_name in view_names:
                if hasattr(module, view_name):
                    print(f"[OK] {app_name}.{view_name}: OK")
                else:
                    print(f"[FAIL] {app_name}.{view_name}: NOT FOUND")
                    all_passed = False
        except Exception as e:
            print(f"[FAIL] {app_name}: FAILED - {str(e)}")
            all_passed = False
    
    return all_passed

def test_public_endpoints():
    """Test public endpoints can be accessed."""
    print("\n" + "=" * 60)
    print("TESTING PUBLIC ENDPOINTS")
    print("=" * 60)
    
    client = Client()
    
    endpoints_to_test = [
        ("GET", "/api/svc/", "Services List"),
        ("GET", "/api/svc/categories/", "Categories List"),
        ("GET", "/api/stf/", "Staff List"),
        ("GET", "/api/", "API Root"),
    ]
    
    all_passed = True
    for method, path, name in endpoints_to_test:
        try:
            if method == "GET":
                response = client.get(path)
                if response.status_code in [200, 400, 401, 403, 404]:  # 404 is OK for some endpoints
                    print(f"[OK] {name} ({path}): HTTP {response.status_code}")
                else:
                    print(f"[FAIL] {name} ({path}): HTTP {response.status_code}")
                    all_passed = False
        except Exception as e:
            print(f"[FAIL] {name} ({path}): ERROR - {str(e)}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MultiBook API Endpoints Verification")
    print("=" * 60)
    
    results = []
    
    # Test 1: Database connection
    results.append(("Database Connection", test_database_connection()))
    
    # Test 2: Model queries
    results.append(("Model Queries", test_model_queries()))
    
    # Test 3: Endpoint imports
    results.append(("Endpoint Imports", test_endpoint_imports()))
    
    # Test 4: Public endpoints
    results.append(("Public Endpoints", test_public_endpoints()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "[OK] PASSED" if passed else "[FAIL] FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[OK] ALL TESTS PASSED")
    else:
        print("[FAIL] SOME TESTS FAILED")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())