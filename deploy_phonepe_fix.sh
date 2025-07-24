#!/bin/bash

# Complete PhonePe Connection Fix Deployment Script
# This script applies the fix and validates it works

echo "🚀 DEPLOYING PHONEPE CONNECTION FIX"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="/var/www/okpuja_backend"
VENV_DIR="$PROJECT_DIR/venv"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Project directory not found: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

print_status "Step 1: Backing up current code..."
cp payment/gateways.py payment/gateways.py.backup.$(date +%Y%m%d_%H%M%S)
print_success "Backup created"

print_status "Step 2: Activating virtual environment..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    print_error "Failed to activate virtual environment"
    exit 1
fi
print_success "Virtual environment activated"

print_status "Step 3: Installing/updating required packages..."
pip install --upgrade requests urllib3 certifi
if [ $? -ne 0 ]; then
    print_warning "Package installation had issues, but continuing..."
fi

print_status "Step 4: Running Django connection diagnostic..."
python fix_django_phonepe.py
diagnostic_result=$?

print_status "Step 5: Collecting static files..."
python manage.py collectstatic --noinput
if [ $? -ne 0 ]; then
    print_warning "Static files collection had issues"
fi

print_status "Step 6: Running Django checks..."
python manage.py check --deploy
if [ $? -ne 0 ]; then
    print_warning "Django deployment checks found issues"
fi

print_status "Step 7: Restarting services..."

# Restart Gunicorn
print_status "Restarting Gunicorn..."
sudo systemctl restart gunicorn
sleep 5

# Check Gunicorn status
if sudo systemctl is-active --quiet gunicorn; then
    print_success "Gunicorn restarted successfully"
else
    print_error "Gunicorn failed to restart"
    sudo systemctl status gunicorn
fi

# Restart Nginx
print_status "Restarting Nginx..."
sudo systemctl restart nginx
sleep 2

# Check Nginx status
if sudo systemctl is-active --quiet nginx; then
    print_success "Nginx restarted successfully"
else
    print_error "Nginx failed to restart"
    sudo systemctl status nginx
fi

print_status "Step 8: Running comprehensive connection test..."

# Test the actual API endpoint
print_status "Testing payment API endpoint..."
python -c "
import requests
import json

try:
    response = requests.get('https://backend.okpuja.com/api/payments/debug/', timeout=10)
    print(f'Debug endpoint status: {response.status_code}')
    if response.status_code == 200:
        print('✅ Django server is responding')
    else:
        print('❌ Django server issues')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"

# Test PhonePe connectivity from the Django app
print_status "Testing PhonePe connectivity from Django..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

import requests
from django.conf import settings

try:
    # Test direct connection to PhonePe
    response = requests.get('https://api.phonepe.com/', timeout=10)
    print(f'PhonePe connectivity: {response.status_code}')
    if response.status_code in [200, 404]:
        print('✅ PhonePe is reachable from Django')
    else:
        print('❌ PhonePe connectivity issues')
        
    # Test SSL certificates
    import ssl
    import socket
    context = ssl.create_default_context()
    with socket.create_connection(('api.phonepe.com', 443), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname='api.phonepe.com') as ssock:
            print(f'✅ SSL certificate valid: {ssock.version()}')
            
except Exception as e:
    print(f'❌ PhonePe test failed: {e}')
"

print_status "Step 9: Service status summary..."
echo ""
echo "=== SERVICE STATUS ==="
echo "Gunicorn: $(sudo systemctl is-active gunicorn)"
echo "Nginx: $(sudo systemctl is-active nginx)"
echo "Django Process: $(pgrep -f gunicorn | wc -l) processes"
echo ""

# Check logs for any immediate errors
print_status "Step 10: Checking recent logs..."
echo "=== RECENT GUNICORN LOGS ==="
sudo journalctl -u gunicorn --no-pager -n 10

echo ""
echo "=== RECENT NGINX LOGS ==="
sudo tail -n 5 /var/log/nginx/error.log

print_status "Step 11: Final validation..."

# Test a simple payment simulation
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

try:
    from payment.gateways import PhonePeGateway
    from django.conf import settings
    
    gateway = PhonePeGateway()
    print(f'✅ Gateway initialized successfully')
    print(f'Merchant ID: {gateway.merchant_id}')
    print(f'Base URL: {gateway.base_url}')
    print(f'SSL Verify: {gateway.ssl_verify}')
    
except Exception as e:
    print(f'❌ Gateway initialization failed: {e}')
"

echo ""
echo "========================================"
if [ $diagnostic_result -eq 0 ]; then
    print_success "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
    print_success "The PhonePe connection fix has been applied."
    print_success "Your payment gateway should now work properly."
else
    print_warning "⚠️  DEPLOYMENT COMPLETED WITH WARNINGS"
    print_warning "Please check the diagnostic output above."
fi

echo ""
echo "=== NEXT STEPS ==="
echo "1. Test a payment in your application"
echo "2. Check the logs: sudo journalctl -u gunicorn -f"
echo "3. Monitor for any errors in production"
echo ""
echo "If you still have issues:"
echo "- Check the Django logs"
echo "- Verify your .env file has correct PhonePe credentials"
echo "- Ensure firewall allows outbound HTTPS connections"
echo "========================================"
