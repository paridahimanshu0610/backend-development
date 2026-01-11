#!/bin/sh
set -e

echo "Waiting for database..."

until pg_isready -h "$DATABASE_HOSTNAME" -p "$DATABASE_PORT" -U "$DATABASE_USERNAME"; do
  sleep 2
done

echo "Database is ready"

alembic upgrade head

exec uvicorn app.orm_main:app --host 0.0.0.0 --port 8000 --reload