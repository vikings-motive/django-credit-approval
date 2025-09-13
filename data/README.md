# Data Directory

This directory should contain the Excel files for initial data ingestion.

## Required Files

Place the following Excel files in this directory before running data ingestion:

### 1. customer_data.xlsx
Should contain the following columns:
- `customer_id` - Unique identifier for the customer
- `first_name` - Customer's first name
- `last_name` - Customer's last name
- `age` - Customer's age (optional, defaults to 25 if missing)
- `phone_number` - Customer's phone number
- `monthly_salary` - Customer's monthly income
- `approved_limit` - Pre-approved credit limit
- `current_debt` - Current outstanding debt (optional, defaults to 0)

### 2. loan_data.xlsx
Should contain the following columns:
- `customer_id` or `customer` - Reference to customer ID
- `loan_id` - Unique identifier for the loan
- `loan_amount` - Principal loan amount
- `tenure` - Loan duration in months
- `interest_rate` - Annual interest rate percentage
- `monthly_repayment` or `monthly_payment` or `emi` - Monthly EMI amount
- `emis_paid_on_time` - Number of EMIs paid on time
- `date_of_approval` or `start_date` - Loan start date
- `end_date` - Loan end date

## Data Ingestion

After placing the Excel files, run the ingestion command:

```bash
# From the project root directory
docker compose exec web python manage.py ingest_data

# Or if running locally
python manage.py ingest_data --sync
```

## Sample Data Format

### Customer Data Example:
| customer_id | first_name | last_name | age | phone_number | monthly_salary | approved_limit | current_debt |
|------------|------------|-----------|-----|--------------|----------------|----------------|--------------|
| 1          | John       | Doe       | 30  | 9876543210   | 50000          | 1800000        | 0            |
| 2          | Jane       | Smith     | 28  | 9876543211   | 75000          | 2700000        | 250000       |

### Loan Data Example:
| customer_id | loan_id | loan_amount | tenure | interest_rate | monthly_repayment | emis_paid_on_time | start_date | end_date   |
|------------|---------|-------------|--------|---------------|-------------------|-------------------|------------|------------|
| 1          | 101     | 200000      | 12     | 10.5          | 17639            | 6                 | 2024-01-01 | 2024-12-31 |
| 2          | 102     | 500000      | 24     | 12.0          | 23536            | 18                | 2023-07-01 | 2025-06-30 |

## Notes

- Ensure date formats are consistent (YYYY-MM-DD recommended)
- Phone numbers should be numeric without special characters
- All monetary values should be positive numbers
- The ingestion script handles both column name variations mentioned above