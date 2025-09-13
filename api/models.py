from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Customer(models.Model):
    """Customer model - stores basic customer information"""
    # Personal details
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField(default=25, validators=[MinValueValidator(18)])
    phone_number = models.CharField(max_length=20, db_index=True)
    
    # Financial details - using DecimalField for precision
    monthly_salary = models.DecimalField(
        max_digits=12, decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )  # Monthly income
    approved_limit = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )  # Max loan amount they can get (36 * monthly_salary)
    current_debt = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )  # Total current outstanding loans
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Loan(models.Model):
    """Loan model - stores loan information for each customer"""
    # Link to customer
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='loans', db_index=True
    )
    
    # Loan details - using DecimalField for precision
    loan_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )  # Principal amount
    tenure = models.IntegerField(
        validators=[MinValueValidator(1)]
    )  # Loan duration in months
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]  
    )  # Annual interest rate percentage
    monthly_repayment = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )  # EMI amount
    
    # Payment tracking
    emis_paid_on_time = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )  # Number of EMIs paid on time
    
    # Date tracking
    start_date = models.DateField()  # When loan was disbursed
    end_date = models.DateField(db_index=True)  # When loan should be fully repaid
    
    class Meta:
        indexes = [
            models.Index(fields=['customer', 'end_date']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"Loan #{self.id} - {self.customer.first_name} - ₹{self.loan_amount}"
