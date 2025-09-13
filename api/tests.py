from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from datetime import date
from django.db import connection
from decimal import Decimal

from .helpers import calculate_monthly_installment, round_to_lakh, calculate_credit_score
from .models import Customer, Loan


class HelpersTestCase(TestCase):
    def test_emi_calculation_example(self):
        # Example: ₹100,000 at 12% for 12 months ≈ ₹8,884.88
        emi = calculate_monthly_installment(100000, 12, 12)
        self.assertAlmostEqual(float(emi), 8884.88, places=2)

    def test_round_to_lakh(self):
        from decimal import Decimal
        self.assertEqual(round_to_lakh(145000), Decimal('100000'))
        self.assertEqual(round_to_lakh(155000), Decimal('200000'))

    def test_credit_score_hard_fail_when_over_limit(self):
        c = Customer.objects.create(
            first_name='A', last_name='B', age=30, phone_number='123',
            monthly_salary=50000, approved_limit=100000, current_debt=0
        )
        # Loan that is active and exceeds approved limit
        Loan.objects.create(
            customer=c, loan_amount=120000, tenure=12, interest_rate=10,
            monthly_repayment=10000, start_date=date.today(), end_date=date.today()
        )
        score = calculate_credit_score(c, list(c.loans.all()))
        self.assertEqual(score, 0)


class ApiEndpointsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_and_check_eligibility_flow(self):
        # Register
        reg_payload = {
            "first_name": "John",
            "last_name": "Doe",
            "age": 30,
            "monthly_income": 50000,
            "phone_number": "9876543210",
        }
        r = self.client.post('/register', reg_payload, format='json')
        self.assertEqual(r.status_code, 201)
        customer_id = r.data['customer_id']

        # Check eligibility
        elig_payload = {
            "customer_id": customer_id,
            "loan_amount": 200000,
            "interest_rate": 10.5,
            "tenure": 12,
        }
        e = self.client.post('/check-eligibility', elig_payload, format='json')
        self.assertEqual(e.status_code, 200)
        self.assertIn('monthly_installment', e.data)
        self.assertIn('corrected_interest_rate', e.data)

    def test_create_loan_when_eligible(self):
        # Create a customer with no loans
        reg_payload = {
            "first_name": "Jane",
            "last_name": "Smith",
            "age": 28,
            "monthly_income": 80000,
            "phone_number": "9999999999",
        }
        r = self.client.post('/register', reg_payload, format='json')
        self.assertEqual(r.status_code, 201)
        customer_id = r.data['customer_id']

        # Create loan
        loan_payload = {
            "customer_id": customer_id,
            "loan_amount": 100000,
            "interest_rate": 12,
            "tenure": 12,
        }
        l = self.client.post('/create-loan', loan_payload, format='json')
        self.assertIn(l.status_code, (200, 201))
        self.assertIn('loan_approved', l.data)

    def test_phone_number_validation(self):
        # Test invalid phone numbers
        invalid_phones = [
            "123",  # Too short
            "12345678901234567890",  # Too long
            "123-456-7890",  # Contains dashes
            "(123) 456-7890",  # Contains special chars
            "123 456 7890",  # Contains spaces
            "abcdefghij",  # Contains letters
        ]
        
        for phone in invalid_phones:
            reg_payload = {
                "first_name": "Test",
                "last_name": "User",
                "age": 25,
                "monthly_income": 50000,
                "phone_number": phone,
            }
            r = self.client.post('/register', reg_payload, format='json')
            self.assertEqual(r.status_code, 400, f"Phone {phone} should be invalid")
            self.assertIn('phone_number', r.data)
        
        # Test valid phone numbers
        valid_phones = [
            "9876543210",  # 10 digits
            "919876543210",  # 12 digits with country code
            "123456789012345",  # 15 digits max
        ]
        
        for i, phone in enumerate(valid_phones):
            reg_payload = {
                "first_name": f"Test{i}",
                "last_name": f"User{i}",
                "age": 25,
                "monthly_income": 50000,
                "phone_number": phone,
            }
            r = self.client.post('/register', reg_payload, format='json')
            self.assertEqual(r.status_code, 201, f"Phone {phone} should be valid")

    def test_sequence_reset_after_ingestion(self):
        """Test that PK sequences are properly reset after manual ID insertion."""
        # Simulate what happens during ingestion - create with explicit ID
        customer = Customer.objects.create(
            id=1000,  # High explicit ID
            first_name="Ingested",
            last_name="Customer",
            age=30,
            phone_number="9876543210",
            monthly_salary=Decimal('50000'),
            approved_limit=Decimal('1800000')
        )
        
        # Reset sequence (this is what our ingestion task does)
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT setval(pg_get_serial_sequence('api_customer', 'id'), 
                       COALESCE((SELECT MAX(id) FROM api_customer), 1), true);
            """)
        
        # Now try to register a new customer via API - should not get IntegrityError
        reg_payload = {
            "first_name": "New",
            "last_name": "Customer",
            "age": 25,
            "monthly_income": 60000,
            "phone_number": "9876543211",
        }
        r = self.client.post('/register', reg_payload, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertGreater(r.data['customer_id'], 1000)  # Should get ID > 1000
