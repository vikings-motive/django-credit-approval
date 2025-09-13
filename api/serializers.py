from rest_framework import serializers
from rest_framework.validators import RegexValidator
from decimal import Decimal
import re

class RegisterSerializer(serializers.Serializer):
    """Serializer for customer registration with enhanced validation"""
    first_name = serializers.CharField(
        max_length=100,
        error_messages={
            'required': 'First name is required',
            'blank': 'First name cannot be blank',
            'max_length': 'First name cannot exceed 100 characters'
        }
    )
    last_name = serializers.CharField(
        max_length=100,
        error_messages={
            'required': 'Last name is required',
            'blank': 'Last name cannot be blank',
            'max_length': 'Last name cannot exceed 100 characters'
        }
    )
    age = serializers.IntegerField(
        min_value=18, 
        max_value=100,
        error_messages={
            'required': 'Age is required',
            'min_value': 'Minimum age is 18 years',
            'max_value': 'Maximum age is 100 years'
        }
    )
    monthly_income = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        min_value=Decimal('1000'),
        max_value=Decimal('9999999999.99'),
        error_messages={
            'required': 'Monthly income is required',
            'min_value': 'Monthly income must be at least ₹1,000',
            'max_value': 'Monthly income cannot exceed ₹9,999,999,999.99',
            'invalid': 'Invalid income format. Please enter a valid number'
        }
    )
    phone_number = serializers.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\d{10,15}$',
                message='Phone number must be 10-15 digits only, no spaces or special characters'
            )
        ],
        error_messages={
            'required': 'Phone number is required',
            'blank': 'Phone number cannot be blank'
        }
    )
    
    def validate_first_name(self, value):
        """Validate first name contains only letters and spaces"""
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError('First name can only contain letters and spaces')
        return value.strip().title()
    
    def validate_last_name(self, value):
        """Validate last name contains only letters and spaces"""
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError('Last name can only contain letters and spaces')
        return value.strip().title()
    
    def validate_phone_number(self, value):
        """Additional phone number validation"""
        # Remove any accidental spaces or dashes
        cleaned = re.sub(r'[\s\-()]', '', value)
        if not cleaned.isdigit():
            raise serializers.ValidationError('Phone number must contain only digits')
        if len(cleaned) < 10:
            raise serializers.ValidationError('Phone number must be at least 10 digits')
        if len(cleaned) > 15:
            raise serializers.ValidationError('Phone number cannot exceed 15 digits')
        return cleaned


class LoanSerializer(serializers.Serializer):
    """Serializer for loan eligibility check and creation with enhanced validation"""
    customer_id = serializers.IntegerField(
        min_value=1,
        error_messages={
            'required': 'Customer ID is required',
            'min_value': 'Invalid customer ID',
            'invalid': 'Customer ID must be a valid number'
        }
    )
    loan_amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        min_value=Decimal('1000'),
        max_value=Decimal('9999999999.99'),
        error_messages={
            'required': 'Loan amount is required',
            'min_value': 'Minimum loan amount is ₹1,000',
            'max_value': 'Maximum loan amount is ₹9,999,999,999.99',
            'invalid': 'Invalid loan amount format'
        }
    )
    interest_rate = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        min_value=Decimal('0'), 
        max_value=Decimal('100'),
        error_messages={
            'required': 'Interest rate is required',
            'min_value': 'Interest rate cannot be negative',
            'max_value': 'Interest rate cannot exceed 100%',
            'invalid': 'Invalid interest rate format'
        }
    )
    tenure = serializers.IntegerField(
        min_value=1,
        max_value=360,  # Max 30 years
        error_messages={
            'required': 'Loan tenure is required',
            'min_value': 'Minimum tenure is 1 month',
            'max_value': 'Maximum tenure is 360 months (30 years)',
            'invalid': 'Tenure must be a valid number of months'
        }
    )
    
    def validate(self, data):
        """Cross-field validation"""
        # Check if loan amount is reasonable for the tenure
        if data['loan_amount'] < Decimal('10000') and data['tenure'] > 12:
            raise serializers.ValidationError(
                'Small loan amounts (< ₹10,000) cannot have tenure > 12 months'
            )
        
        # Check if interest rate is reasonable
        if data['interest_rate'] > Decimal('50'):
            raise serializers.ValidationError(
                'Interest rates above 50% require special approval. Please contact support.'
            )
        
        return data
