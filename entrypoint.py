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


def start_server():
    """Start the Django development server."""
    print("Starting server...")
    os.execvp(sys.executable, [sys.executable, "manage.py", "runserver", "0.0.0.0:8000"])


if __name__ == "__main__":
    if wait_for_db():
        run_migrations()
        start_server()
    else:
        sys.exit(1)
