# Credit Approval System

A simple Django-based REST API for managing customer loans and credit approvals.

## Features

- Customer registration with automatic credit limit calculation
- Credit score-based loan eligibility checking
- Loan creation with interest rate correction
- View loan details and active loans
- Background data ingestion from Excel files

## Tech Stack

- Django 4.2+
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Docker & Docker Compose

## Setup Instructions

### Prerequisites

- Docker Desktop installed and running
- Excel files (`customer_data.xlsx` and `loan_data.xlsx`) placed in `data/` directory

### Running the Application

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bck_alm_1
   ```

2. **Place Excel files**
   - Copy `customer_data.xlsx` and `loan_data.xlsx` to the `data/` directory

3. **Start all services**
   ```bash
   docker compose up --build -d
   ```
   Note: Migrations run automatically on startup.

4. **Load initial data from Excel files**
   
   Option 1: Using management command (recommended)
   ```bash
   # Async via Celery (default)
   docker compose exec web python manage.py ingest_data
   
   # Or synchronously if Celery is not available
   docker compose exec web python manage.py ingest_data --sync
   ```
   
   Option 2: Using Django shell
   ```bash
   docker compose exec web python manage.py shell
   >>> from api.tasks import ingest_data
   >>> ingest_data.delay()  # Async
   # OR
   >>> ingest_data()  # Sync
   ```

## API Endpoints

### 1. Register Customer
- **URL**: `/register`
- **Method**: POST
- **Body**:
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "age": 30,
    "monthly_income": 50000,
    "phone_number": "9876543210"
  }
  ```

### 2. Check Loan Eligibility
- **URL**: `/check-eligibility`
- **Method**: POST
- **Body**:
  ```json
  {
    "customer_id": 1,
    "loan_amount": 500000,
    "interest_rate": 10.5,
    "tenure": 24
  }
  ```

### 3. Create Loan
- **URL**: `/create-loan`
- **Method**: POST
- **Body**:
  ```json
  {
    "customer_id": 1,
    "loan_amount": 500000,
    "interest_rate": 10.5,
    "tenure": 24
  }
  ```

### 4. View Loan Details
- **URL**: `/view-loan/<loan_id>`
- **Method**: GET

### 5. View Customer's Active Loans
- **URL**: `/view-loans/<customer_id>`
- **Method**: GET

## Business Logic

### Credit Score Calculation
- Base score: 50 points
- On-time payments: +30 points maximum
- Recent loans: -5 points per loan in current year
- If current debt > approved limit: score = 0

### Loan Approval Rules
- Credit Score > 50: Approve with any interest rate
- 30 < Score ≤ 50: Minimum 12% interest rate
- 10 < Score ≤ 30: Minimum 16% interest rate
- Score ≤ 10: Reject loan
- Total EMIs must not exceed 50% of monthly salary

### EMI Calculation
Uses compound interest formula:
```
EMI = P × r × (1+r)^n / ((1+r)^n - 1)
```
Where:
- P = Principal amount
- r = Monthly interest rate
- n = Number of months

## Stopping the Application

```bash
docker compose down
```

## Running Tests

```bash
# Run all unit tests
docker compose exec web python manage.py test

# Run specific test modules
docker compose exec web python manage.py test api.tests.HelpersTestCase
docker compose exec web python manage.py test api.tests.ApiEndpointsTestCase
```

## Viewing Logs

```bash
# Django logs
docker compose logs web

# Celery worker logs
docker compose logs worker

# Database logs
docker compose logs db
```
