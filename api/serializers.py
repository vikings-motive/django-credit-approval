from rest_framework import serializers
from rest_framework.validators import RegexValidator
from decimal import Decimal

class RegisterSerializer(serializers.Serializer):
    """Serializer for customer registration"""
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField(min_value=18, max_value=100)
    monthly_income = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    phone_number = serializers.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\d{10,15}$',
                message='Phone number must be 10-15 digits only, no spaces or special characters'
            )
        ]
    )


class LoanSerializer(serializers.Serializer):
    """Serializer for loan eligibility check and creation"""
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0'), max_value=Decimal('100'))
    tenure = serializers.IntegerField(min_value=1)  # in months
