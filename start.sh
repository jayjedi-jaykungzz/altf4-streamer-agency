#!/bin/sh
# start.sh - รัน seed (idempotent) แล้ว start waitress
set -e

echo "============================================"
echo "  ALTF4 Streamer Agency - Starting..."
echo "============================================"

# Set env
export DATABASE_PATH=${DATABASE_PATH:-/tmp/agency.db}
export FLASK_DEBUG=0

# Seed (idempotent — skip if already seeded)
echo "📁 Database: $DATABASE_PATH"
python /opt/render/project/src/app/seed_for_prod.py

echo "🚀 Starting waitress..."
exec waitress-serve --host=0.0.0.0 --port=$PORT main:app
