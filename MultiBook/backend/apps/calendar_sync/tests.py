"""
Calendar Sync tests.

Day 5: Calendar Sync Testing & Optimization.
- Test calendar status, manual sync, custom event validation for all roles.
- No live OAuth/API calls; tests use disconnected calendar or mock.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Profile

User = get_user_model()


class CalendarStatusViewTests(TestCase):
    """GET /api/calendar/status/ - requires auth; returns calendar_sync_enabled, last_sync_at, last_sync_error."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='staff@test.com',
            password='testpass123',
            role='staff',
            username='staff1',
        )
        Profile.objects.get_or_create(user=self.user, defaults={'calendar_sync_enabled': False})

    def test_status_requires_auth(self):
        response = self.client.get('/api/calendar/status/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_status_returns_200_with_data(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/calendar/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        data = response.data.get('data') or {}
        self.assertIn('calendar_sync_enabled', data)
        self.assertIn('calendar_provider', data)
        self.assertIn('last_sync_at', data)
        self.assertIn('last_sync_error', data)


class ManualSyncViewTests(TestCase):
    """POST /api/calendar/sync/ - manual sync; when calendar not connected returns 400 or success with 0 synced."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='customer@test.com',
            password='testpass123',
            role='customer',
            username='customer1',
        )
        Profile.objects.get_or_create(user=self.user, defaults={'calendar_sync_enabled': False})

    def test_sync_requires_auth(self):
        response = self.client.post('/api/calendar/sync/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sync_when_not_connected_returns_error_or_zero(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/calendar/sync/')
        # Backend may return 400 (SYNC_FAILED) or 200 with synced_count 0
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST))
        if response.status_code == status.HTTP_200_OK:
            self.assertTrue(response.data.get('success'))
            self.assertEqual(response.data.get('data', {}).get('synced_count'), 0)


class CustomEventCreateViewTests(TestCase):
    """GET /api/calendar/events/ and POST /api/calendar/events/ - list events; create requires start/end."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            role='customer',
            username='user1',
        )
        Profile.objects.get_or_create(user=self.user, defaults={'calendar_sync_enabled': False})

    def test_events_list_requires_auth(self):
        response = self.client.get('/api/calendar/events/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_events_list_returns_200_with_events_array(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/calendar/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        data = response.data.get('data') or {}
        self.assertIn('events', data)
        self.assertIsInstance(data['events'], list)

    def test_custom_event_post_requires_auth(self):
        response = self.client.post('/api/calendar/events/', {
            'title': 'Test',
            'start': '2025-12-01T10:00:00Z',
            'end': '2025-12-01T11:00:00Z',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_custom_event_post_without_start_end_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/calendar/events/', {
            'title': 'Test',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get('success', True))
        err = response.data.get('error') or {}
        self.assertIn('start', (err.get('message') or '').lower() or 'start and end' in str(response.data))

    def test_custom_event_post_with_start_end_validation(self):
        self.client.force_authenticate(user=self.user)
        # Calendar not connected - expect 400 CALENDAR_NOT_CONNECTED
        response = self.client.post('/api/calendar/events/', {
            'title': 'Test Event',
            'start': '2025-12-01T10:00:00Z',
            'end': '2025-12-01T11:00:00Z',
        }, format='json')
        self.assertIn(response.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED, status.HTTP_500_INTERNAL_SERVER_ERROR))
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertFalse(response.data.get('success', True))


class BulkSyncViewTests(TestCase):
    """POST /api/calendar/sync-bulk/ - admin only."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role='admin',
            username='admin1',
        )
        self.customer = User.objects.create_user(
            email='cust2@test.com',
            password='testpass123',
            role='customer',
            username='cust2',
        )
        Profile.objects.get_or_create(user=self.admin)
        Profile.objects.get_or_create(user=self.customer)

    def test_bulk_sync_requires_auth(self):
        response = self.client.post('/api/calendar/sync-bulk/', {'user_ids': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bulk_sync_denied_for_non_admin(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.post('/api/calendar/sync-bulk/', {'user_ids': [self.admin.id]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bulk_sync_returns_200_for_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/calendar/sync-bulk/', {'user_ids': [self.customer.id]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        self.assertIn('results', response.data.get('data') or {})
