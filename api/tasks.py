from celery import shared_task
import pandas as pd
from datetime import datetime
from .models import Customer, Loan


@shared_task
def ingest_data():
    """
    Load Excel data into database.
    This task reads customer_data.xlsx and loan_data.xlsx from /app/data/
    and populates the database.
    """
    print("Starting data ingestion...")
    
    # Load customer data
    try:
        customers_df = pd.read_excel('/app/data/customer_data.xlsx')
        # Normalize column names: strip whitespace, lowercase, replace spaces with underscores
        customers_df.columns = (
            customers_df.columns
            .str.strip()
            .str.lower()
            .str.replace(' ', '_', regex=False)
        )
        print(f"Found {len(customers_df)} customers to load")
        print(f"Columns: {list(customers_df.columns)}")
        
        for _, row in customers_df.iterrows():
            # Create or update customer
            Customer.objects.update_or_create(
                id=int(row['customer_id']),
                defaults={
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'phone_number': str(row['phone_number']),
                    'monthly_salary': float(row['monthly_salary']),
                    'approved_limit': float(row['approved_limit']),
                    'current_debt': float(row.get('current_debt', 0)),  # Read from Excel if present
                    'age': int(row['age']) if pd.notna(row.get('age')) else 25
                }
            )
        print(f"Successfully loaded {len(customers_df)} customers")
        
    except Exception as e:
        print(f"Error loading customers: {e}")
        return f"Failed to load customers: {e}"
    
    # Load loan data
    try:
        loans_df = pd.read_excel('/app/data/loan_data.xlsx')
        # Normalize column names
        loans_df.columns = (
            loans_df.columns
            .str.strip()
            .str.lower()
            .str.replace(' ', '_', regex=False)
        )
        print(f"Found {len(loans_df)} loans to load")
        print(f"Columns: {list(loans_df.columns)}")
        
        for _, row in loans_df.iterrows():
            # Find customer - handle both 'customer_id' and 'customer id' variations
            customer_id_key = 'customer_id' if 'customer_id' in row else 'customer'  
            customer = Customer.objects.filter(id=int(row[customer_id_key])).first()
            
            if customer:
                # Convert dates - handle various column name formats
                start_date_key = 'date_of_approval' if 'date_of_approval' in row else 'start_date'
                start_date = pd.to_datetime(row[start_date_key]).date()
                end_date = pd.to_datetime(row['end_date']).date()
                
                # Create or update loan
                Loan.objects.update_or_create(
                    id=int(row['loan_id']),
                    defaults={
                        'customer': customer,
                        'loan_amount': float(row['loan_amount']),
                        'tenure': int(row['tenure']),
                        'interest_rate': float(row['interest_rate']),
                        'monthly_repayment': float(row.get('monthly_repayment', row.get('monthly_payment', row.get('emi', 0)))),
                        'emis_paid_on_time': int(row.get('emis_paid_on_time', 0)),
                        'start_date': start_date,
                        'end_date': end_date
                    }
                )
            else:
                print(f"Customer {row.get(customer_id_key)} not found for loan {row['loan_id']}")
                
        print(f"Successfully loaded {len(loans_df)} loans")
        
    except Exception as e:
        print(f"Error loading loans: {e}")
        return f"Failed to load loans: {e}"
    
    return "Data ingestion completed successfully"
