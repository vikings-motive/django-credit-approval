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

## API Documentation

### Swagger/OpenAPI Documentation
Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/swagger/` or `http://localhost:8000/`
- ReDoc: `http://localhost:8000/redoc/`
- OpenAPI Schema: `http://localhost:8000/swagger.json`

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

### 6. Health Check Endpoints
- **Basic Health**: `/health/` - Simple health status
- **Detailed Health**: `/health/detailed/` - Checks all dependencies (DB, Redis, Celery)
- **Readiness Check**: `/health/ready/` - Kubernetes readiness probe
- **Liveness Check**: `/health/live/` - Kubernetes liveness probe

## Business Logic

### Credit Score Calculation
- Base score: 50 points
- On-time payments: +30 points maximum
- Recent loans: -5 points per loan in current year
- If current debt > approved limit: score = 0

### Loan Approval Rules
- If credit_rating > 50: Approve loan with any interest rate
- If 50 > credit_rating > 30: Approve loans with interest rate > 12%
- If 30 > credit_rating > 10: Approve loans with interest rate > 16%
- If 10 > credit_rating: Don't approve any loans
- If sum of all current EMIs > 50% of monthly salary: Don't approve any loans

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

# Follow logs in real-time
docker compose logs -f web worker
```

## Recent Improvements

### Testing
- ✅ Comprehensive test coverage for all business rules
- ✅ Edge case testing (boundary values, invalid inputs)
- ✅ Concurrent loan creation testing
- ✅ Credit score component testing
- ✅ Interest rate correction validation

### API Documentation
- ✅ Swagger/OpenAPI integration with drf-yasg
- ✅ Interactive API testing interface
- ✅ Auto-generated API documentation

### Data Validation
- ✅ Enhanced input validation with detailed error messages
- ✅ Name validation (letters only)
- ✅ Phone number sanitization
- ✅ Cross-field validation for loans
- ✅ Boundary value checks

### Monitoring & Health
- ✅ Comprehensive logging configuration
- ✅ Health check endpoints for all services
- ✅ Kubernetes-ready health probes
- ✅ Service dependency monitoring

### Docker Optimization
- ✅ Multi-stage build for smaller images
- ✅ Non-root user for security
- ✅ Health checks for all containers
- ✅ Optimized dependency caching
- ✅ Log volume persistence

### Security
- ✅ Non-root container execution
- ✅ Input sanitization
- ✅ Environment variable configuration
- ✅ Secure defaults
