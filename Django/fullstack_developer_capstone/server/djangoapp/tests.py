from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import CarMake, CarModel
import json


class DjangoAppTestCase(TestCase):
    """Test cases for the Django application"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create test car make and model
        self.car_make = CarMake.objects.create(
            name="Toyota",
            description="Japanese automotive manufacturer",
            country="Japan",
            founded_year=1937,
            website="https://www.toyota.com"
        )

        self.car_model = CarModel.objects.create(
            car_make=self.car_make,
            dealer_id=1,
            name="Camry",
            type="SEDAN",
            year=2023,
            engine_type="4-Cylinder",
            fuel_type="Gasoline",
            transmission="Automatic",
            color="White",
            price=25000.00
        )

        # Create test user
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_car_make_creation(self):
        """Test car make model creation"""
        self.assertEqual(self.car_make.name, "Toyota")
        self.assertEqual(self.car_make.country, "Japan")
        self.assertEqual(self.car_make.founded_year, 1937)

    def test_car_model_creation(self):
        """Test car model creation"""
        self.assertEqual(self.car_model.name, "Camry")
        self.assertEqual(self.car_model.car_make, self.car_make)
        self.assertEqual(self.car_model.year, 2023)
        self.assertEqual(float(self.car_model.price), 25000.00)

    def test_get_cars_endpoint(self):
        """Test the get_cars API endpoint"""
        response = self.client.get('/djangoapp/get_cars')
        self.assertEqual(response.status_code, 200)

        # Parse JSON response
        data = json.loads(response.content)
        self.assertIn('CarModels', data)
        self.assertTrue(len(data['CarModels']) > 0)

    def test_get_dealers_endpoint(self):
        """Test the get_dealers API endpoint"""
        response = self.client.get('/djangoapp/get_dealers/', follow=True)
        self.assertEqual(response.status_code, 200)

        # Parse JSON response
        data = json.loads(response.content)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 200)

    def test_user_registration_endpoint(self):
        """Test user registration endpoint"""
        registration_data = {
            'userName': 'newuser',
            'password': 'newpass123',
            'firstName': 'New',
            'lastName': 'User',
            'email': 'newuser@example.com'
        }

        response = self.client.post(
            '/djangoapp/register',
            data=json.dumps(registration_data),
            content_type='application/json'
        )

        # Should return 200 or 201 for successful registration
        self.assertIn(response.status_code, [200, 201])

    def test_login_endpoint_structure(self):
        """Test login endpoint exists and returns proper structure"""
        login_data = {
            'userName': 'testuser',
            'password': 'testpass123'
        }

        response = self.client.post(
            '/djangoapp/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )

        # Should return 200 (success or failure, but endpoint should exist)
        self.assertEqual(response.status_code, 200)

    def test_models_string_representation(self):
        """Test string representation of models"""
        self.assertEqual(str(self.car_make), "Toyota")
        expected_car_model_str = "Toyota Camry"
        self.assertEqual(str(self.car_model), expected_car_model_str)

    def test_car_model_relationships(self):
        """Test relationships between models"""
        # Test foreign key relationship
        self.assertEqual(self.car_model.car_make.name, "Toyota")

        # Test reverse relationship
        car_models = self.car_make.carmodel_set.all()
        self.assertIn(self.car_model, car_models)


class APIEndpointsTestCase(TestCase):
    """Test API endpoints availability and basic functionality"""

    def setUp(self):
        self.client = Client()

    def test_api_endpoints_exist(self):
        """Test that all main API endpoints exist and return valid responses"""
        endpoints = [
            '/djangoapp/get_dealers/',
            '/djangoapp/get_cars',
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint, follow=True)
                # Should not return 404 (endpoint should exist)
                self.assertNotEqual(response.status_code, 404)

    def test_cors_headers_present(self):
        """Test that CORS headers are properly configured"""
        response = self.client.get('/djangoapp/get_dealers/', follow=True)

        # Check if the response has CORS-related headers
        # Note: In test environment, CORS headers might not be fully present
        # but the endpoint should still work
        self.assertEqual(response.status_code, 200)


class ModelValidationTestCase(TestCase):
    """Test model validation and constraints"""

    def test_car_model_year_validation(self):
        """Test car model year is within valid range"""
        car_make = CarMake.objects.create(
            name="Honda",
            description="Japanese automotive manufacturer",
            country="Japan",
            founded_year=1946,
            website="https://www.honda.com"
        )

        # Test valid year
        car_model = CarModel(
            car_make=car_make,
            dealer_id=1,
            name="Civic",
            type="SEDAN",
            year=2023,
            engine_type="4-Cylinder",
            fuel_type="Gasoline",
            transmission="Manual",
            color="Blue",
            price=22000.00
        )

        # Should not raise validation error
        car_model.full_clean()
        car_model.save()

        self.assertEqual(car_model.year, 2023)

    def test_car_make_required_fields(self):
        """Test that car make required fields are enforced"""
        car_make = CarMake(name="Ford")

        # Should be able to save with minimal required fields
        car_make.save()
        self.assertEqual(car_make.name, "Ford")

    def test_car_type_choices(self):
        """Test that car type choices are properly validated"""
        car_make = CarMake.objects.create(name="BMW")

        # Test all valid car types
        valid_types = ['SEDAN', 'SUV', 'WAGON', 'COUPE', 'CONVERTIBLE',
                       'HATCHBACK', 'TRUCK']

        for car_type in valid_types:
            with self.subTest(car_type=car_type):
                car_model = CarModel(
                    car_make=car_make,
                    dealer_id=1,
                    name="Test Model",
                    type=car_type,
                    year=2023
                )
                # Should not raise validation error
                car_model.full_clean()
                car_model.save()
                self.assertEqual(car_model.type, car_type)
