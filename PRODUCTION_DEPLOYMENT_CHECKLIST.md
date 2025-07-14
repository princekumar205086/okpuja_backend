# Production Deployment Checklist for OkPuja PhonePe Integration

## Pre-Deployment Checklist

### 1. Environment Configuration
- [ ] Update `.env` file with production values:
  ```bash
  PHONEPE_ENV=PRODUCTION
  PHONEPE_CLIENT_ID=your_production_client_id
  PHONEPE_CLIENT_SECRET=73e5f6e1-1da3-403e-8168-da15fdffbd7d
  
  PHONEPE_REDIRECT_URL=https://api.okpuja.com/api/payments/webhook/phonepe/
  PHONEPE_CALLBACK_URL=https://api.okpuja.com/api/payments/webhook/phonepe/
  PHONEPE_FAILED_REDIRECT_URL=https://okpuja.com/failedbooking
  PHONEPE_SUCCESS_REDIRECT_URL=https://okpuja.com/confirmbooking/
  FRONTEND_BASE_URL=https://okpuja.com
  
  DEBUG=False
  ALLOWED_HOSTS=okpuja.com,api.okpuja.com,www.okpuja.com
  ```

### 2. SSL/HTTPS Setup
- [ ] SSL certificate installed for `okpuja.com`
- [ ] SSL certificate installed for `api.okpuja.com`
- [ ] Force HTTPS redirect configured
- [ ] Test SSL using: https://www.ssllabs.com/ssltest/

### 3. DNS Configuration
- [ ] `okpuja.com` points to frontend server
- [ ] `api.okpuja.com` points to Django backend server
- [ ] `www.okpuja.com` redirects to `okpuja.com`
- [ ] DNS propagation completed (test with: `nslookup okpuja.com`)

### 4. PhonePe Dashboard Configuration
- [ ] Login to PhonePe Production Dashboard
- [ ] Update webhook URL to: `https://api.okpuja.com/api/payments/webhook/phonepe/`
- [ ] Configure callback authentication username/password
- [ ] Update environment variables with callback credentials
- [ ] Test webhook connection from PhonePe dashboard

## Deployment Steps

### 1. Server Setup
```bash
# Clone/update repository
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Test configuration
python manage.py test_phonepe
```

### 2. Web Server Configuration

#### Nginx Configuration Example
```nginx
server {
    listen 80;
    server_name api.okpuja.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name api.okpuja.com;
    
    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/static/files/;
        expires 30d;
    }
}
```

#### Gunicorn Configuration
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn okpuja_backend.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### 3. Service Configuration

#### Systemd Service (Ubuntu/CentOS)
Create `/etc/systemd/system/okpuja-backend.service`:
```ini
[Unit]
Description=OkPuja Backend Django Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/okpuja_backend
Environment=PATH=/path/to/venv/bin
EnvironmentFile=/path/to/.env
ExecStart=/path/to/venv/bin/gunicorn okpuja_backend.wsgi:application --bind 0.0.0.0:8000
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable okpuja-backend
sudo systemctl start okpuja-backend
sudo systemctl status okpuja-backend
```

## Post-Deployment Testing

### 1. Basic Health Checks
- [ ] API accessible at `https://api.okpuja.com`
- [ ] Admin panel accessible at `https://api.okpuja.com/admin/`
- [ ] Frontend accessible at `https://okpuja.com`
- [ ] HTTPS working correctly (no mixed content warnings)

### 2. PhonePe Integration Tests
```bash
# Test PhonePe configuration
python manage.py test_phonepe

# Test payment flow (if you have test data)
curl -X POST https://api.okpuja.com/api/payments/payments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"booking": 1, "amount": "100.00", "method": "PHONEPE"}'
```

### 3. Webhook Testing
- [ ] Test webhook endpoint: `https://api.okpuja.com/api/payments/webhook/phonepe/`
- [ ] Verify webhook can receive POST requests
- [ ] Check logs for any webhook processing errors
- [ ] Test from PhonePe dashboard webhook test feature

### 4. Error Monitoring
- [ ] Set up log monitoring (e.g., CloudWatch, ELK stack)
- [ ] Configure error alerting
- [ ] Monitor payment transaction logs
- [ ] Set up uptime monitoring

## Security Checklist

### 1. Django Security
- [ ] `DEBUG=False` in production
- [ ] `SECRET_KEY` is strong and unique
- [ ] `ALLOWED_HOSTS` properly configured
- [ ] Database credentials secured
- [ ] Static files served efficiently

### 2. PhonePe Security
- [ ] Client secret stored securely
- [ ] Webhook authentication configured
- [ ] Callback username/password set
- [ ] API keys not exposed in logs

### 3. Server Security
- [ ] Firewall configured (only 80, 443, SSH open)
- [ ] Regular security updates enabled
- [ ] SSH key-based authentication
- [ ] Fail2ban or similar intrusion prevention

## Monitoring & Maintenance

### 1. Regular Checks
- [ ] Monitor payment success rates
- [ ] Check webhook delivery rates
- [ ] Monitor API response times
- [ ] Review error logs weekly

### 2. Backup Strategy
- [ ] Database backups configured
- [ ] Application code backups
- [ ] Environment variables backed up securely
- [ ] SSL certificates backup

### 3. Performance Monitoring
- [ ] Set up APM (Application Performance Monitoring)
- [ ] Monitor database performance
- [ ] Track API endpoint performance
- [ ] Monitor payment processing times

## Rollback Plan

If issues occur after deployment:

1. **Immediate Rollback:**
   ```bash
   # Switch back to UAT environment
   sed -i 's/PHONEPE_ENV=PRODUCTION/PHONEPE_ENV=UAT/' .env
   sed -i 's/api.okpuja.com/localhost:8000/g' .env
   sudo systemctl restart okpuja-backend
   ```

2. **PhonePe Dashboard:**
   - Revert webhook URL to development
   - Switch back to test credentials

3. **DNS (if needed):**
   - Point domains back to old servers
   - Wait for DNS propagation

## Support Contacts

- **PhonePe Support:** [PhonePe Integration Team]
- **Hosting Provider:** [Your hosting provider support]
- **SSL Provider:** [Your SSL certificate provider]
- **DNS Provider:** [Your domain registrar/DNS provider]

---

**Note:** Test all changes in a staging environment before production deployment.
