from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from datetime import date
from dateutil.relativedelta import relativedelta
from django.db import transaction
from decimal import Decimal
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .models import Customer, Loan
from .serializers import RegisterSerializer, LoanSerializer
from .helpers import calculate_credit_score, calculate_monthly_installment, round_to_lakh

# Get logger for this module
logger = logging.getLogger('api')


@swagger_auto_schema(
    method='post',
    request_body=RegisterSerializer,
    responses={
        201: openapi.Response(
            description="Customer registered successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'customer_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                    'age': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'monthly_income': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'approved_limit': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: "Invalid input data"
    },
    operation_description="Register a new customer. Approved limit = 36 * monthly_income (rounded to nearest lakh)"
)
@api_view(['POST'])
@throttle_classes([AnonRateThrottle])
def register(request):
    """
    Register a new customer.
    Approved limit = 36 * monthly_income (rounded to nearest lakh)
    """
    serializer = RegisterSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Calculate approved limit: 36 times monthly income, rounded to lakh
    approved_limit = round_to_lakh(data['monthly_income'] * 36)
    
    # Create customer
    customer = Customer.objects.create(
        first_name=data['first_name'],
        last_name=data['last_name'],
        age=data['age'],
        phone_number=data['phone_number'],
        monthly_salary=data['monthly_income'],
        approved_limit=approved_limit
    )
    
    # Return response
    return Response({
        'customer_id': customer.id,
        'name': f"{customer.first_name} {customer.last_name}",
        'age': customer.age,
        'monthly_income': customer.monthly_salary,
        'approved_limit': customer.approved_limit,
        'phone_number': customer.phone_number
    }, status=status.HTTP_201_CREATED)


def _check_loan_eligibility(customer_id, loan_amount, interest_rate, tenure):
    """
    Internal function to check loan eligibility.
    Returns a dict with eligibility details.
    """
    # Get customer
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return {'error': 'Customer not found'}
    
    # Get all loans for this customer
    loans = list(customer.loans.all())
    
    # Calculate credit score
    score = calculate_credit_score(customer, loans)
    
    # Determine eligibility based on score
    approval = False
    corrected_interest_rate = interest_rate
    
    if score > 50:
        # Good score - approve with any rate
        approval = True
    elif score > 30:
        # Medium score - need at least 12% interest
        if interest_rate >= 12:
            approval = True
        else:
            corrected_interest_rate = 12
            approval = True
    elif score > 10:
        # Low score - need at least 16% interest
        if interest_rate >= 16:
            approval = True
        else:
            corrected_interest_rate = 16
            approval = True
    else:
        # Very low score - reject
        approval = False
    
    # Calculate EMI with corrected interest rate
    monthly_installment = calculate_monthly_installment(
        loan_amount,
        corrected_interest_rate,
        tenure
    )
    
    # Check if total EMIs exceed 50% of salary
    if approval:
        today = date.today()
        active_loans = [loan for loan in loans if loan.end_date >= today]
        current_total_emi = sum((loan.monthly_repayment for loan in active_loans), Decimal('0'))
        
        if current_total_emi + monthly_installment > customer.monthly_salary * Decimal('0.5'):
            approval = False
    
    return {
        'customer': customer,
        'customer_id': customer.id,
        'approval': approval,
        'interest_rate': interest_rate,
        'corrected_interest_rate': corrected_interest_rate,
        'tenure': tenure,
        'monthly_installment': monthly_installment,
        'loans': loans
    }


@api_view(['POST'])
@throttle_classes([AnonRateThrottle])
def check_eligibility(request):
    """
    Check loan eligibility based on credit score.
    
    Credit score rules:
    - Score > 50: Approve with any interest rate
    - 30 < Score <= 50: Approve only if interest >= 12%
    - 10 < Score <= 30: Approve only if interest >= 16%
    - Score <= 10: Reject
    
    Also check: Total EMIs should not exceed 50% of monthly salary
    """
    serializer = LoanSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Use internal function
    result = _check_loan_eligibility(
        data['customer_id'],
        data['loan_amount'],
        data['interest_rate'],
        data['tenure']
    )
    
    # Check for errors
    if 'error' in result:
        return Response(
            {'error': result['error']}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Return response
    return Response({
        'customer_id': result['customer_id'],
        'approval': result['approval'],
        'interest_rate': result['interest_rate'],
        'corrected_interest_rate': result['corrected_interest_rate'],
        'tenure': result['tenure'],
        'monthly_installment': result['monthly_installment']
    })


@api_view(['POST'])
@throttle_classes([AnonRateThrottle])
def create_loan(request):
    """
    Create a new loan if eligible.
    First checks eligibility, then creates loan if approved.
    Uses atomic transaction to ensure data consistency.
    """
    serializer = LoanSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Check eligibility using internal function
    eligibility = _check_loan_eligibility(
        data['customer_id'],
        data['loan_amount'],
        data['interest_rate'],
        data['tenure']
    )
    
    # Check for errors
    if 'error' in eligibility:
        return Response(
            {'error': eligibility['error']}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # If not approved, return rejection
    if not eligibility['approval']:
        return Response({
            'loan_id': None,
            'customer_id': eligibility['customer_id'],
            'loan_approved': False,
            'message': 'Loan cannot be approved based on credit score',
            'monthly_installment': 0
        })
    
    # Use atomic transaction to ensure consistency
    with transaction.atomic():
        # Lock the customer row to prevent concurrent modifications
        customer = Customer.objects.select_for_update().get(id=data['customer_id'])
        
        # Re-check eligibility with locked customer data to prevent race conditions
        today = date.today()
        active_loans = customer.loans.filter(end_date__gte=today)
        current_total_emi = sum((loan.monthly_repayment for loan in active_loans), Decimal('0'))
        new_emi = eligibility['monthly_installment']
        
        # Final affordability check with locked data
        if current_total_emi + new_emi > customer.monthly_salary * Decimal('0.5'):
            return Response({
                'loan_id': None,
                'customer_id': customer.id,
                'loan_approved': False,
                'message': 'Total EMIs would exceed 50% of monthly salary',
                'monthly_installment': 0
            })
        
        # Check if total debt would exceed approved limit
        total_current_debt = sum((loan.loan_amount for loan in active_loans), Decimal('0'))
        if total_current_debt + data['loan_amount'] > customer.approved_limit:
            return Response({
                'loan_id': None,
                'customer_id': customer.id,
                'loan_approved': False,
                'message': 'Loan would exceed approved credit limit',
                'monthly_installment': 0
            })
        
        # Calculate dates
        start_date = today
        end_date = start_date + relativedelta(months=data['tenure'])
        
        # Create loan with corrected interest rate from eligibility check
        loan = Loan.objects.create(
            customer=customer,
            loan_amount=data['loan_amount'],
            tenure=data['tenure'],
            interest_rate=eligibility['corrected_interest_rate'],
            monthly_repayment=eligibility['monthly_installment'],
            start_date=start_date,
            end_date=end_date
        )
        
        # Update customer's current debt
        customer.current_debt = total_current_debt + data['loan_amount']
        customer.save(update_fields=['current_debt'])
    
    return Response({
        'loan_id': loan.id,
        'customer_id': customer.id,
        'loan_approved': True,
        'message': 'Loan has been approved',
        'monthly_installment': loan.monthly_repayment
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def view_loan(request, loan_id):
    """
    View details of a specific loan.
    """
    try:
        loan = Loan.objects.get(id=loan_id)
    except Loan.DoesNotExist:
        return Response(
            {'error': 'Loan not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    customer = loan.customer
    
    return Response({
        'loan_id': loan.id,
        'customer': {
            'id': customer.id,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone_number': customer.phone_number,
            'age': customer.age
        },
        'loan_amount': loan.loan_amount,
        'interest_rate': loan.interest_rate,
        'monthly_installment': loan.monthly_repayment,
        'tenure': loan.tenure
    })


@api_view(['GET'])
def view_loans(request, customer_id):
    """
    View all current/active loans of a customer.
    Shows only loans that haven't ended yet.
    """
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get active loans (end date is in future)
    today = date.today()
    active_loans = customer.loans.filter(end_date__gte=today)
    
    loans_data = []
    for loan in active_loans:
        # Calculate how many months have passed
        months_passed = (today.year - loan.start_date.year) * 12 + \
                       (today.month - loan.start_date.month)
        
        # Calculate repayments left
        repayments_left = max(0, loan.tenure - months_passed)
        
        loans_data.append({
            'loan_id': loan.id,
            'loan_amount': loan.loan_amount,
            'interest_rate': loan.interest_rate,
            'monthly_installment': loan.monthly_repayment,
            'repayments_left': repayments_left
        })
    
    return Response(loans_data)
