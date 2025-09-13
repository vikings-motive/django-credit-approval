#!/usr/bin/env python
"""
Entrypoint script for the Django application.
Waits for database, runs migrations, then starts the server.
"""
import os
import sys
import time
import subprocess


def wait_for_db():
    """Wait for database to be ready."""
    print("Waiting for database...")
    max_retries = 30
    for i in range(max_retries):
        try:
            # Try to run a simple Django command that requires DB
            result = subprocess.run(
                [sys.executable, "manage.py", "showmigrations", "--plan"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("Database is ready!")
                return True
        except Exception:
            pass
        
        if i < max_retries - 1:
            print(f"Database not ready yet, waiting... ({i+1}/{max_retries})")
            time.sleep(2)
    
    print("ERROR: Database did not become ready in time!")
    return False


def run_migrations():
    """Run database migrations."""
    print("Running migrations...")
    result = subprocess.run(
        [sys.executable, "manage.py", "migrate", "--noinput"],
        capture_output=False
    )
    if result.returncode != 0:
        print("ERROR: Failed to run migrations!")
        sys.exit(1)
    print("Migrations completed successfully!")


def check_and_ingest_data():
    """Check if data files exist and queue ingestion if not already loaded."""
    import os
    from pathlib import Path
    
    data_dir = Path("/app/data")
    customer_file = data_dir / "customer_data.xlsx"
    loan_file = data_dir / "loan_data.xlsx"
    
    # Check if both data files exist
    if customer_file.exists() and loan_file.exists():
        print("Found Excel data files, checking if data needs ingestion...")
        
        # Check if data is already loaded by querying customer count
        result = subprocess.run(
            [sys.executable, "manage.py", "shell", "-c", 
             "from api.models import Customer; print(Customer.objects.count())"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            try:
                count = int(result.stdout.strip())
                if count == 0:
                    print("No customers found, queuing data ingestion...")
                    # Queue the ingestion task asynchronously
                    subprocess.run(
                        [sys.executable, "manage.py", "ingest_data"],
                        capture_output=False
                    )
                    print("Data ingestion queued successfully!")
                else:
                    print(f"Found {count} existing customers, skipping ingestion.")
            except ValueError:
                print("Could not determine customer count, skipping auto-ingestion.")
        else:
            print("Could not check database state, skipping auto-ingestion.")
    else:
        print("Excel data files not found in /app/data, skipping auto-ingestion.")


def start_server():
    """Start the production server with gunicorn."""
    print("Starting server with gunicorn...")
    # Use gunicorn for production, fallback to runserver if not available
    gunicorn_result = subprocess.run(
        ["which", "gunicorn"],
        capture_output=True
    )
    
    if gunicorn_result.returncode == 0:
        # Use gunicorn (production)
        os.execvp("gunicorn", [
            "gunicorn",
            "credit_approval.wsgi:application",
            "--bind", "0.0.0.0:8000",
            "--workers", "2",
            "--timeout", "120",
            "--access-logfile", "-",
            "--error-logfile", "-"
        ])
    else:
        # Fallback to development server
        print("Gunicorn not found, using development server...")
        os.execvp(sys.executable, [sys.executable, "manage.py", "runserver", "0.0.0.0:8000"])


if __name__ == "__main__":
    if wait_for_db():
        run_migrations()
        check_and_ingest_data()
        start_server()
    else:
        sys.exit(1)
