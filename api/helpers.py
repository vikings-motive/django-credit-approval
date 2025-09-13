import math
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

def calculate_credit_score(customer, loans):
    """
    Calculate credit score (0-100) for a customer based on their loan history.
    
    Components:
    1. If current loans exceed approved limit -> score = 0 (hard fail)
    2. Base score: 50 points
    3. On-time payment history: +30 points max
    4. Number of past loans penalty: -2 points per loan (shows dependency)
    5. Current year loan activity: -5 points per recent loan
    6. Loan volume vs approved limit: -10 points if total historic > 2x approved limit
    7. Keep final score between 0 and 100
    """
    # Check if customer has too much debt
    today = date.today()
    active_loans = [loan for loan in loans if loan.end_date >= today]
    total_current_debt = sum((loan.loan_amount for loan in active_loans), Decimal('0'))
    
    # Hard rule: If debt exceeds approved limit, score is 0
    if total_current_debt > customer.approved_limit:
        return 0
    
    # Start with base score
    score = 50
    
    # Component 1: Add points for on-time payments (max +30)
    if loans:
        total_emis = sum(loan.tenure for loan in loans)
        paid_on_time = sum(loan.emis_paid_on_time for loan in loans)
        
        if total_emis > 0:
            on_time_percentage = paid_on_time / total_emis
            score += int(on_time_percentage * 30)
    
    # Component 2: Penalty for number of past loans (-2 per loan, max -20)
    num_past_loans = len(loans)
    loan_count_penalty = min(20, num_past_loans * 2)  # Cap at -20
    score -= loan_count_penalty
    
    # Component 3: Penalty for loans in current year (-5 per loan)
    current_year_loans = [loan for loan in loans 
                          if loan.start_date.year == today.year]
    score -= len(current_year_loans) * 5
    
    # Component 4: Penalty for excessive total loan volume
    # If total historic loan amounts > 2x approved limit, penalize
    total_historic_volume = sum((loan.loan_amount for loan in loans), Decimal('0'))
    if total_historic_volume > Decimal('2') * customer.approved_limit:
        score -= 10
    
    # Component 5: Bonus for low current utilization (+5 if using < 30% of limit)
    utilization_ratio = total_current_debt / customer.approved_limit if customer.approved_limit > 0 else Decimal('0')
    if utilization_ratio < Decimal('0.3'):
        score += 5
    
    # Keep score in valid range (0-100)
    return max(0, min(100, score))


def calculate_monthly_installment(principal, annual_rate, tenure_months):
    """
    Calculate EMI using compound interest formula with Decimal precision.
    
    Formula: EMI = P × r × (1+r)^n / ((1+r)^n - 1)
    Where:
    - P = Principal loan amount
    - r = Monthly interest rate (annual rate / 12 / 100)
    - n = Number of months
    
    Example: ₹100,000 at 12% for 12 months = ₹8,884.88 per month
    Returns: Decimal for precision
    """
    # Convert to Decimal for precision
    principal = Decimal(str(principal))
    annual_rate = Decimal(str(annual_rate))
    tenure_months = int(tenure_months)
    
    # Convert annual rate to monthly rate
    monthly_rate = annual_rate / Decimal('12') / Decimal('100')
    
    # If interest rate is 0, just divide principal by tenure
    if monthly_rate == 0:
        emi = principal / Decimal(tenure_months)
        return emi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Apply compound interest formula using Decimal arithmetic
    # Note: For power operation with Decimal, we convert to float temporarily
    compound_factor = Decimal(str(math.pow(float(1 + monthly_rate), tenure_months)))
    emi = principal * monthly_rate * compound_factor / (compound_factor - 1)
    
    # Round to 2 decimal places and return as Decimal
    return emi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def round_to_lakh(amount):
    """
    Round amount to nearest lakh (100,000) using Decimal for precision.
    
    Examples:
    - 145,000 -> 100,000 (1 lakh)
    - 155,000 -> 200,000 (2 lakhs)
    - 1,850,000 -> 1,900,000 (19 lakhs)
    Returns: Decimal for precision
    """
    amount = Decimal(str(amount))
    lakh = Decimal('100000')
    rounded_lakhs = (amount / lakh).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return rounded_lakhs * lakh
