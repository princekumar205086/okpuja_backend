#!/bin/bash

# Production Migration Fix Script
# Run this script on your production server to fix the duplicate column migration issue

echo "🔧 Starting production migration fix..."
echo "========================================"

# Change to project directory
cd /opt/api.okpuja.com

# Step 1: Check current migration status
echo "📋 Current migration status:"
python manage.py showmigrations astrology

echo ""
echo "🔧 Step 1: Applying fake migration for duplicate column fix..."

# Step 2: Fake apply the problematic migration
python manage.py migrate astrology 0003_add_google_meet_fields --fake

echo ""
echo "🔧 Step 2: Applying all remaining migrations..."

# Step 3: Apply all migrations
python manage.py migrate

echo ""
echo "📋 Final migration status:"
python manage.py showmigrations astrology

echo ""
echo "🔧 Step 3: Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "✅ Production migration fix complete!"
echo "🎉 Your Django backend should now be ready to deploy!"

# Optional: Show all migration status
echo ""
echo "📊 All apps migration status:"
python manage.py showmigrations
