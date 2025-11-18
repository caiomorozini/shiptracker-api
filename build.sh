#!/usr/bin/env bash
# Render build script

set -o errexit  # exit on error

echo "=========================================="
echo "� Starting build process..."
echo "=========================================="

echo ""
echo "�📦 Step 1/3: Installing dependencies..."
pip install uv --no-cache-dir
uv pip install --system --no-cache -e .

echo ""
echo "🗄️  Step 2/3: Running database migrations..."
echo "Command: alembic upgrade head"
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Migration failed! Build will abort."
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Step 3/3: Build complete!"
echo "=========================================="
echo ""
echo "Next: Render will start the application"
echo "=========================================="
