#!/usr/bin/env bash
# Render Pre-Deploy script - only runs migrations
# Dependencies are already installed in the Docker image

set -o errexit  # exit on error

echo "=========================================="
echo "🗄️  Running database migrations..."
echo "=========================================="

echo ""
echo "Command: alembic upgrade head"
alembic upgrade head

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migrations completed successfully!"
    echo "=========================================="
else
    echo ""
    echo "❌ Migration failed! Deploy will abort."
    echo "=========================================="
    exit 1
fi
