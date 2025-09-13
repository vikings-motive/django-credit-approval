#!/bin/bash

# Database Restore Script for Credit Approval System
# Usage: ./restore_db.sh <backup_file> [environment]
# Example: ./restore_db.sh ./backups/backup_dev_credit_approval_db_20240101_120000.sql.gz dev

set -e  # Exit on error

# Check arguments
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <backup_file> [environment]"
    echo "Example: $0 ./backups/backup_dev_credit_approval_db_20240101_120000.sql.gz dev"
    exit 1
fi

BACKUP_FILE="$1"
ENVIRONMENT=${2:-dev}

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file $BACKUP_FILE not found!"
    exit 1
fi

# Load environment variables
if [ "$ENVIRONMENT" = "prod" ]; then
    ENV_FILE=".env.prod"
    COMPOSE_FILE="docker-compose.prod.yml"
else
    ENV_FILE=".env"
    COMPOSE_FILE="docker-compose.yml"
fi

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file $ENV_FILE not found!"
    exit 1
fi

# Load environment variables
export $(cat $ENV_FILE | grep -v '^#' | xargs)

echo "================================"
echo "Database Restore Tool"
echo "================================"
echo "Environment: $ENVIRONMENT"
echo "Database: $POSTGRES_DB"
echo "Backup file: $BACKUP_FILE"
echo ""
echo "⚠️  WARNING: This will REPLACE ALL DATA in the database!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Create temporary uncompressed file if backup is compressed
TEMP_FILE=""
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "Decompressing backup file..."
    TEMP_FILE="${BACKUP_FILE%.gz}"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    RESTORE_FILE="$TEMP_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

echo "Starting database restore..."

# Stop all connections to the database
echo "Stopping application services..."
docker compose -f $COMPOSE_FILE stop web worker celery-beat 2>/dev/null || true

# Drop and recreate the database
echo "Dropping existing database..."
docker compose -f $COMPOSE_FILE exec -T db psql \
    -U $POSTGRES_USER \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$POSTGRES_DB' AND pid <> pg_backend_pid();" \
    postgres

docker compose -f $COMPOSE_FILE exec -T db psql \
    -U $POSTGRES_USER \
    -c "DROP DATABASE IF EXISTS $POSTGRES_DB;" \
    postgres

echo "Creating new database..."
docker compose -f $COMPOSE_FILE exec -T db psql \
    -U $POSTGRES_USER \
    -c "CREATE DATABASE $POSTGRES_DB;" \
    postgres

# Restore the database
echo "Restoring database from backup..."
docker compose -f $COMPOSE_FILE exec -T db psql \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB \
    < "$RESTORE_FILE"

# Clean up temporary file
if [ -n "$TEMP_FILE" ]; then
    rm -f "$TEMP_FILE"
fi

# Run migrations to ensure schema is up to date
echo "Running Django migrations..."
docker compose -f $COMPOSE_FILE exec -T web python manage.py migrate

# Reset sequences (important after restore)
echo "Resetting database sequences..."
docker compose -f $COMPOSE_FILE exec -T web python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('''
        SELECT setval(pg_get_serial_sequence('api_customer', 'id'), 
               COALESCE((SELECT MAX(id) FROM api_customer), 1), true);
    ''')
    cursor.execute('''
        SELECT setval(pg_get_serial_sequence('api_loan', 'id'), 
               COALESCE((SELECT MAX(id) FROM api_loan), 1), true);
    ''')
    print('Sequences reset successfully')
"

# Restart services
echo "Restarting application services..."
docker compose -f $COMPOSE_FILE start web worker celery-beat 2>/dev/null || true

echo ""
echo "✅ Database restore completed successfully!"
echo ""
echo "Summary:"
echo "- Database: $POSTGRES_DB"
echo "- Environment: $ENVIRONMENT"
echo "- Restored from: $BACKUP_FILE"
echo ""
echo "Please verify the application is working correctly."