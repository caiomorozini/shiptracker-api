#!/usr/bin/env bash
# Render build script

set -o errexit  # exit on error

echo "📦 Installing dependencies..."
pip install uv
uv pip install -e .

echo "🗄️ Running database migrations..."
alembic upgrade head

echo "✅ Build complete!"
