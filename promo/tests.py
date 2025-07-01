# promo/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from puja.models import PujaService
from astrology.models import AstrologyService
from .models import PromoCode, PromoCodeUsage

User = get_user_model()

class PromoCodeModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
        self.puja_service = PujaService.objects.create(
            title='Test Puja',
            description='Test description'
        )
        self.astrology_service = AstrologyService.objects.create(
            service_title='Test Astrology',
            service_type='Horoscope',
            service_price=50.00,
            service_desc='Test description'
        )

    def test_create_percentage_promo_code(self):
        promo = PromoCode.objects.create(
            code='TEST10',
            discount=10,
            discount_type='PERCENT',
            expiry_date=timezone.now() + timezone.timedelta(days=30),
            created_by=self.user
        )
        self.assertEqual(promo.discount_type, 'PERCENT')
        self.assertTrue(promo.is_valid())

    def test_create_flat_promo_code(self):
        promo = PromoCode.objects.create(
            code='FLAT50',
            discount=50,
            discount_type='FLAT',
            expiry_date=timezone.now() + timezone.timedelta(days=30),
            created_by=self.user
        )
        self.assertEqual(promo.discount_type, 'FLAT')
        self.assertEqual(promo.apply_discount(100), 50)

    def test_promo_code_validation(self):
        # Test expired promo code
        expired_promo = PromoCode.objects.create(
            code='EXPIRED',
            discount=10,
            discount_type='PERCENT',
            expiry_date=timezone.now() - timezone.timedelta(days=1),
            created_by=self.user
        )
        is_valid, message = expired_promo.is_valid()
        self.assertFalse(is_valid)
        self.assertEqual(message, "Promo code has expired")

class PromoCodeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            username='adminuser'
        )
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            username='testuser'
        )
        self.promo = PromoCode.objects.create(
            code='TEST20',
            discount=20,
            discount_type='PERCENT',
            expiry_date=timezone.now() + timezone.timedelta(days=30),
            created_by=self.admin
        )

    def test_admin_create_promo_code(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            'code': 'NEWPROMO',
            'discount': 15,
            'discount_type': 'PERCENT',
            'expiry_date': (timezone.now() + timezone.timedelta(days=30)).isoformat(),
            'usage_limit': 100
        }
        response = self.client.post('/api/promo/admin/promo-codes/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PromoCode.objects.count(), 2)

    def test_public_promo_code_list(self):
        response = self.client.get('/api/promo/promo-codes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_validate_promo_code(self):
        response = self.client.get('/api/promo/promo-codes/validate/?code=TEST20')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])

    def test_user_promo_codes(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/promo/user/promo-codes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)