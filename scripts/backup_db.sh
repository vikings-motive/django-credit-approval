#!/bin/bash

# Database Backup Script for Credit Approval System
# Usage: ./backup_db.sh [environment]
# Environment can be: dev (default) or prod

set -e  # Exit on error

# Configuration
ENVIRONMENT=${1:-dev}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

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

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup filename
BACKUP_FILE="${BACKUP_DIR}/backup_${ENVIRONMENT}_${POSTGRES_DB}_${TIMESTAMP}.sql"
BACKUP_FILE_GZ="${BACKUP_FILE}.gz"

echo "Starting database backup for $ENVIRONMENT environment..."
echo "Database: $POSTGRES_DB"
echo "Backup file: $BACKUP_FILE_GZ"

# Perform backup using docker compose
docker compose -f $COMPOSE_FILE exec -T db pg_dump \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB \
    --verbose \
    --no-owner \
    --no-acl \
    --format=plain \
    --encoding=UTF8 \
    > "$BACKUP_FILE"

# Check if backup was successful
if [ $? -eq 0 ] && [ -s "$BACKUP_FILE" ]; then
    echo "Backup completed successfully!"
    
    # Compress the backup
    gzip "$BACKUP_FILE"
    echo "Backup compressed to: $BACKUP_FILE_GZ"
    
    # Calculate file size
    SIZE=$(du -h "$BACKUP_FILE_GZ" | cut -f1)
    echo "Backup size: $SIZE"
    
    # Clean old backups (older than RETENTION_DAYS)
    echo "Cleaning backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "backup_${ENVIRONMENT}_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    
    # List remaining backups
    echo ""
    echo "Current backups:"
    ls -lh "$BACKUP_DIR"/backup_${ENVIRONMENT}_*.sql.gz 2>/dev/null || echo "No backups found"
    
    echo ""
    echo "✅ Backup completed successfully!"
else
    echo "❌ Backup failed!"
    rm -f "$BACKUP_FILE"  # Clean up empty file
    exit 1
fi

# Optional: Upload to cloud storage (uncomment and configure as needed)
# AWS S3 example:
# aws s3 cp "$BACKUP_FILE_GZ" "s3://your-backup-bucket/credit-approval/${ENVIRONMENT}/"

# Google Cloud Storage example:
# gsutil cp "$BACKUP_FILE_GZ" "gs://your-backup-bucket/credit-approval/${ENVIRONMENT}/"

# Azure Blob Storage example:
# az storage blob upload --file "$BACKUP_FILE_GZ" --container-name backups --name "credit-approval/${ENVIRONMENT}/$(basename $BACKUP_FILE_GZ)"