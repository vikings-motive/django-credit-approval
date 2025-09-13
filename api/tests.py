from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from datetime import date
from dateutil.relativedelta import relativedelta
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

    def test_credit_score_components(self):
        """Test all credit score calculation components."""
        from dateutil.relativedelta import relativedelta
        
        # Create customer with specific approved limit
        customer = Customer.objects.create(
            first_name='Test', last_name='User', age=30,
            phone_number='1234567890', monthly_salary=100000,
            approved_limit=3600000, current_debt=0
        )
        
        # Test 1: Customer with no loans should get base score
        score = calculate_credit_score(customer, [])
        self.assertEqual(score, 50)  # Base score
        
        # Test 2: Add loan with perfect payment history
        loan1 = Loan.objects.create(
            customer=customer, loan_amount=500000, tenure=12,
            interest_rate=10, monthly_repayment=43957,
            emis_paid_on_time=12,  # All EMIs paid on time
            start_date=date.today() - relativedelta(months=13),
            end_date=date.today() - relativedelta(months=1)
        )
        score = calculate_credit_score(customer, [loan1])
        # Base 50 + 30 (perfect payment) - 2 (1 loan) = 78
        self.assertGreaterEqual(score, 75)
        
        # Test 3: Current year loan penalty
        loan2 = Loan.objects.create(
            customer=customer, loan_amount=200000, tenure=6,
            interest_rate=12, monthly_repayment=34693,
            emis_paid_on_time=3,
            start_date=date.today(),
            end_date=date.today() + relativedelta(months=6)
        )
        score = calculate_credit_score(customer, [loan1, loan2])
        # Should be lower due to current year loan
        self.assertLess(score, 75)

    def test_loan_rejection_scenarios(self):
        """Test all loan rejection scenarios per business rules."""
        # Create customer
        customer = Customer.objects.create(
            first_name='Test', last_name='User', age=30,
            phone_number='9999999999', monthly_salary=50000,
            approved_limit=1800000, current_debt=0
        )
        
        # Scenario 1: Credit score = 0 when current loans > approved limit
        Loan.objects.create(
            customer=customer, loan_amount=2000000,  # Exceeds limit
            tenure=24, interest_rate=10, monthly_repayment=92290,
            start_date=date.today(),
            end_date=date.today() + relativedelta(months=24)
        )
        
        payload = {
            "customer_id": customer.id,
            "loan_amount": 100000,
            "interest_rate": 10,
            "tenure": 12
        }
        response = self.client.post('/create-loan', payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['loan_approved'])
        
    def test_interest_rate_correction(self):
        """Test interest rate correction based on credit score slabs."""
        # Create customer with good history
        customer = Customer.objects.create(
            first_name='Good', last_name='Customer', age=35,
            phone_number='8888888888', monthly_salary=80000,
            approved_limit=2880000, current_debt=0
        )
        
        # Give customer loans with moderate payment history
        # This should result in credit score between 30-50
        for i in range(3):
            Loan.objects.create(
                customer=customer, loan_amount=100000, tenure=12,
                interest_rate=10, monthly_repayment=8792,
                emis_paid_on_time=8,  # 66% on-time
                start_date=date.today() - relativedelta(months=15+i*12),
                end_date=date.today() - relativedelta(months=3+i*12)
            )
        
        # Test: Request loan with low interest (should be corrected to 12%)
        payload = {
            "customer_id": customer.id,
            "loan_amount": 200000,
            "interest_rate": 8,  # Too low for credit score
            "tenure": 12
        }
        response = self.client.post('/check-eligibility', payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['interest_rate'], 8)
        self.assertGreaterEqual(response.data['corrected_interest_rate'], 12)
        
    def test_emi_exceeds_50_percent_salary(self):
        """Test loan rejection when EMIs exceed 50% of salary."""
        customer = Customer.objects.create(
            first_name='EMI', last_name='Test', age=28,
            phone_number='7777777777', monthly_salary=60000,
            approved_limit=2160000, current_debt=0
        )
        
        # Create existing loan with EMI = 25000 (41.6% of salary)
        Loan.objects.create(
            customer=customer, loan_amount=500000, tenure=24,
            interest_rate=10, monthly_repayment=25000,
            start_date=date.today(),
            end_date=date.today() + relativedelta(months=24)
        )
        
        # Try to create loan that would push total EMI > 50%
        payload = {
            "customer_id": customer.id,
            "loan_amount": 200000,  # Would add ~9000 EMI
            "interest_rate": 10,
            "tenure": 24
        }
        response = self.client.post('/create-loan', payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['loan_approved'])
        self.assertIn('50%', response.data['message'])
        
    def test_view_loans_repayments_calculation(self):
        """Test correct calculation of repayments_left in view-loans."""
        from dateutil.relativedelta import relativedelta
        
        customer = Customer.objects.create(
            first_name='View', last_name='Test', age=30,
            phone_number='6666666666', monthly_salary=75000,
            approved_limit=2700000, current_debt=0
        )
        
        # Create loan started 5 months ago with 12 month tenure
        loan = Loan.objects.create(
            customer=customer, loan_amount=300000, tenure=12,
            interest_rate=10, monthly_repayment=26374,
            start_date=date.today() - relativedelta(months=5),
            end_date=date.today() + relativedelta(months=7)
        )
        
        response = self.client.get(f'/view-loans/{customer.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['repayments_left'], 7)
        
    def test_concurrent_loan_creation(self):
        """Test handling of concurrent loan creation requests."""
        from django.db import transaction
        import threading
        
        customer = Customer.objects.create(
            first_name='Concurrent', last_name='Test', age=32,
            phone_number='5555555555', monthly_salary=100000,
            approved_limit=3600000, current_debt=0
        )
        
        results = []
        
        def create_loan():
            payload = {
                "customer_id": customer.id,
                "loan_amount": 2000000,  # Each loan is large
                "interest_rate": 10,
                "tenure": 12
            }
            r = self.client.post('/create-loan', payload, format='json')
            results.append(r.data['loan_approved'])
        
        # Try to create 2 loans concurrently
        threads = [threading.Thread(target=create_loan) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Only one should succeed due to limit checks
        approved_count = sum(1 for r in results if r)
        self.assertEqual(approved_count, 1, "Only one loan should be approved")
        
    def test_invalid_customer_id(self):
        """Test handling of invalid customer IDs."""
        # Test check-eligibility with non-existent customer
        payload = {
            "customer_id": 99999,
            "loan_amount": 100000,
            "interest_rate": 10,
            "tenure": 12
        }
        response = self.client.post('/check-eligibility', payload, format='json')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.data)
        
        # Test create-loan with non-existent customer  
        response = self.client.post('/create-loan', payload, format='json')
        self.assertEqual(response.status_code, 404)
        
        # Test view-loans with non-existent customer
        response = self.client.get('/view-loans/99999')
        self.assertEqual(response.status_code, 404)
        
        # Test view-loan with non-existent loan
        response = self.client.get('/view-loan/99999')
        self.assertEqual(response.status_code, 404)
        
    def test_boundary_values(self):
        """Test boundary values for various inputs."""
        # Test minimum age
        payload = {
            "first_name": "Young",
            "last_name": "Person",
            "age": 17,  # Below minimum
            "monthly_income": 50000,
            "phone_number": "4444444444"
        }
        response = self.client.post('/register', payload, format='json')
        # Should fail validation or use default
        
        # Test zero/negative loan amount
        customer = Customer.objects.create(
            first_name='Boundary', last_name='Test', age=30,
            phone_number='3333333333', monthly_salary=50000,
            approved_limit=1800000
        )
        
        payload = {
            "customer_id": customer.id,
            "loan_amount": 0,
            "interest_rate": 10,
            "tenure": 12
        }
        response = self.client.post('/check-eligibility', payload, format='json')
        self.assertEqual(response.status_code, 400)
        
        # Test very high interest rate
        payload['loan_amount'] = 100000
        payload['interest_rate'] = 150  # Above 100%
        response = self.client.post('/check-eligibility', payload, format='json')
        self.assertEqual(response.status_code, 400)
        
        # Test zero tenure
        payload['interest_rate'] = 10
        payload['tenure'] = 0
        response = self.client.post('/check-eligibility', payload, format='json')
        self.assertEqual(response.status_code, 400)
