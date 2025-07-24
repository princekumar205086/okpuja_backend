#!/bin/bash
# Manual Server Setup Script for OkPuja Backend
# Run this once on your VPS: bash setup_server.sh

set -e  # Exit on any error

echo "=== OkPuja Backend Server Setup ==="
echo "Setting up production environment on Ubuntu server..."

# Update system
echo "Updating system packages..."
apt update -y
apt upgrade -y

# Install required packages
echo "Installing required packages..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-full \
    git \
    nginx \
    supervisor \
    curl \
    ufw \
    certbot \
    python3-certbot-nginx

# Create application directory
echo "Creating application directory..."
mkdir -p /opt/backend.okpuja.com
cd /opt/backend.okpuja.com

# Clone repository
echo "Cloning repository..."
if [ -d ".git" ]; then
    echo "Repository already exists, updating..."
    git fetch origin main
    git reset --hard origin/main
else
    git clone https://github.com/princekumar205086/okpuja_backend.git .
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file (you'll need to populate this with your actual values)
if [ ! -f ".env" ]; then
    echo "Creating .env file template..."
    cat > .env << 'ENV_EOF'
# Admin Seeding
ADMIN_EMAIL=admin@okpuja.com
ADMIN_PASSWORD=admin@123
ADMIN_USERNAME=admin

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=okpuja108@gmail.com
EMAIL_HOST_PASSWORD=yxml zsqs llgj qemt
DEFAULT_FROM_EMAIL=okpuja108@gmail.com

# Security & Production Settings
SECRET_KEY=your-super-strong-secret-key-here
DEBUG=False
PRODUCTION_SERVER=True
ALLOWED_HOSTS=localhost,127.0.0.1,api.okpuja.com,backend.okpuja.com,157.173.221.192

# CORS Settings
CORS_ALLOWED_ORIGINS=https://okpuja.com,https://okpuja.com,https://api.okpuja.com,https://backend.okpuja.com

# SMS Configuration (Twilio)
SMS_BACKEND=accounts.sms.backends.twilio.SMSBackend
TWILIO_ACCOUNT_SID=AC2579e0ac56e69dd9cc33459773cb0093
TWILIO_AUTH_TOKEN=f66fe3cf57bb20d2df8e58431e23b7d1
TWILIO_PHONE_NUMBER=+17753068597

# ImageKit Configuration
IMAGEKIT_PUBLIC_KEY=public_a4uvfKCVq2A6bPZIuZlXCmiZzXQ=
IMAGEKIT_PRIVATE_KEY=private_xc9Dht8sDl1Xx3kc43FzP5lWoxw=
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/okpuja

# OTP Configuration
OTP_EXPIRE_MINUTES=15
OTP_LENGTH=6

# PhonePe Payment Gateway Configuration (Production)
PHONEPE_ENV=PRODUCTION
PHONEPE_MERCHANT_ID=M22KEWU5BO1I2
PHONEPE_MERCHANT_KEY=73e5f6e1-1da3-403e-8168-da15fdffbd7d
PHONEPE_SALT_INDEX=1
PHONEPE_BASE_URL=https://api.phonepe.com/apis/hermes

# PhonePe URLs (Updated for production)
PHONEPE_REDIRECT_URL=https://backend.okpuja.com/api/payments/webhook/phonepe/
PHONEPE_CALLBACK_URL=https://backend.okpuja.com/api/payments/webhook/phonepe/
PHONEPE_FAILED_REDIRECT_URL=https://okpuja.com/failedbooking
PHONEPE_SUCCESS_REDIRECT_URL=https://okpuja.com/confirmbooking/

# Enhanced PhonePe Connection Settings (Production Optimized)
PHONEPE_TIMEOUT=120
PHONEPE_MAX_RETRIES=5
PHONEPE_SSL_VERIFY=True

# Frontend Base URL (Production)
FRONTEND_BASE_URL=https://okpuja.com

# Employee Registration
EMPLOYEE_REGISTRATION_CODE=EMP2025OK5

# Database Backup Configuration
DB_BACKUP_STORAGE_TYPE=LOCAL
DB_BACKUP_PATH=backups/
DB_BACKUP_RETENTION_DAYS=7
DB_BACKUP_MAX_FILES=10
DB_BACKUP_AUTO_ENABLED=True
ENV_EOF

    echo "⚠️  .env file created. Please review and update with your actual values!"
fi

# Run Django setup
echo "Running Django migrations and setup..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Create superuser if needed (optional)
echo "You can create a superuser later with: python manage.py createsuperuser"

# Create Gunicorn configuration
echo "Creating Gunicorn configuration..."
mkdir -p /etc/supervisor/conf.d
cat > /etc/supervisor/conf.d/gunicorn_api_okpuja.conf << 'GUNICORN_EOF'
[program:gunicorn_api_okpuja]
command=/opt/backend.okpuja.com/venv/bin/gunicorn --workers 3 --bind unix:/opt/backend.okpuja.com/gunicorn.sock okpuja_backend.wsgi:application
directory=/opt/backend.okpuja.com
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/gunicorn_api_okpuja.log
environment=PATH="/opt/backend.okpuja.com/venv/bin"
GUNICORN_EOF

# Create Nginx configuration
echo "Creating Nginx configuration..."
cat > /etc/nginx/sites-available/backend.okpuja.com << 'NGINX_EOF'
server {
    listen 80;
    server_name backend.okpuja.com 157.173.221.192;

    client_max_body_size 50M;

    location / {
        proxy_pass http://unix:/opt/backend.okpuja.com/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /opt/backend.okpuja.com/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/backend.okpuja.com/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
NGINX_EOF

# Enable site and remove default
echo "Configuring Nginx..."
ln -sf /etc/nginx/sites-available/backend.okpuja.com /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Set proper permissions
echo "Setting permissions..."
chown -R www-data:www-data /opt/backend.okpuja.com
chmod -R 755 /opt/backend.okpuja.com

# Configure firewall
echo "Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 22
ufw allow 80
ufw allow 443

# Test nginx configuration
echo "Testing Nginx configuration..."
nginx -t

# Start services
echo "Starting services..."
supervisorctl reread
supervisorctl update
supervisorctl start gunicorn_api_okpuja
systemctl restart nginx
systemctl enable nginx
systemctl enable supervisor

# Show status
echo ""
echo "=== Service Status ==="
supervisorctl status gunicorn_api_okpuja
systemctl status nginx --no-pager

# Health check
echo ""
echo "=== Health Check ==="
sleep 3
curl -I http://localhost/ || echo "Application may still be starting..."

echo ""
echo "=== Setup Complete! ==="
echo "Your Django application should now be running on:"
echo "  - http://157.173.221.192"
echo "  - http://backend.okpuja.com (if DNS is configured)"
echo ""
echo "Next steps:"
echo "1. Review and update the .env file with your actual values"
echo "2. Set up SSL certificate: certbot --nginx -d backend.okpuja.com"
echo "3. Test your API endpoints"
echo "4. Configure your GitHub Actions secrets for automatic deployment"
echo ""
echo "To check logs:"
echo "  - Application: tail -f /var/log/gunicorn_api_okpuja.log"
echo "  - Nginx: tail -f /var/log/nginx/error.log"
echo ""
echo "To restart services:"
echo "  - Application: supervisorctl restart gunicorn_api_okpuja"
echo "  - Web server: systemctl restart nginx"
