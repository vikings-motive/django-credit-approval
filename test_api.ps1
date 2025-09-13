# Test API endpoints

Write-Host "Testing Credit Approval System API" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green

# 1. Register a new customer
Write-Host "`n1. Registering new customer..." -ForegroundColor Yellow
$registerBody = @{
    first_name = "John"
    last_name = "Doe"
    age = 30
    monthly_income = 75000
    phone_number = "9876543210"
} | ConvertTo-Json

$register = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/register" -ContentType "application/json" -Body $registerBody
Write-Host "Customer registered successfully!" -ForegroundColor Green
Write-Host "Customer ID: $($register.customer_id)"
Write-Host "Name: $($register.name)"
Write-Host "Approved Limit: $($register.approved_limit)"

# 2. Check loan eligibility
Write-Host "`n2. Checking loan eligibility..." -ForegroundColor Yellow
$eligibilityBody = @{
    customer_id = 1
    loan_amount = 500000
    interest_rate = 10.5
    tenure = 24
} | ConvertTo-Json

$eligibility = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/check-eligibility" -ContentType "application/json" -Body $eligibilityBody
Write-Host "Eligibility check complete!" -ForegroundColor Green
Write-Host "Approval: $($eligibility.approval)"
Write-Host "Interest Rate: $($eligibility.interest_rate)"
Write-Host "Corrected Interest Rate: $($eligibility.corrected_interest_rate)"
Write-Host "Monthly Installment: $($eligibility.monthly_installment)"

# 3. Create a loan
Write-Host "`n3. Creating loan..." -ForegroundColor Yellow
$loanBody = @{
    customer_id = 1
    loan_amount = 200000
    interest_rate = 15
    tenure = 12
} | ConvertTo-Json

$loan = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/create-loan" -ContentType "application/json" -Body $loanBody
Write-Host "Loan creation complete!" -ForegroundColor Green
Write-Host "Loan ID: $($loan.loan_id)"
Write-Host "Approved: $($loan.loan_approved)"
Write-Host "Message: $($loan.message)"

# 4. View loan details
Write-Host "`n4. Viewing loan details..." -ForegroundColor Yellow
$loanDetails = Invoke-RestMethod -Method GET -Uri "http://localhost:8000/view-loan/1"
Write-Host "Loan Details:" -ForegroundColor Green
Write-Host "Loan ID: $($loanDetails.loan_id)"
Write-Host "Customer: $($loanDetails.customer.first_name) $($loanDetails.customer.last_name)"
Write-Host "Loan Amount: $($loanDetails.loan_amount)"
Write-Host "Interest Rate: $($loanDetails.interest_rate)"

# 5. View customer's active loans
Write-Host "`n5. Viewing customer's active loans..." -ForegroundColor Yellow
$customerLoans = Invoke-RestMethod -Method GET -Uri "http://localhost:8000/view-loans/1"
Write-Host "Active Loans Count: $($customerLoans.Count)" -ForegroundColor Green
if ($customerLoans.Count -gt 0) {
    $customerLoans | ForEach-Object {
        Write-Host "  Loan ID: $($_.loan_id), Amount: $($_.loan_amount), EMI: $($_.monthly_installment)"
    }
}

Write-Host "`n====================================" -ForegroundColor Green
Write-Host "All tests completed successfully!" -ForegroundColor Green
