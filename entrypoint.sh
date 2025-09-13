#!/bin/sh
set -e

echo "Waiting for database..."
while ! python manage.py showmigrations --plan 2>/dev/null; do
    echo "Database not ready yet, waiting..."
    sleep 2
done

echo "Database is ready!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
