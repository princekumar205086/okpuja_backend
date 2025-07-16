# Production PhonePe Connectivity Issues - Complete Solution Guide

## Problem Analysis
Your PhonePe payment integration works locally but fails on the production server with "Connection refused" errors. This is a common production deployment issue.

## Root Causes
1. **Firewall/Network Restrictions**: Production servers often have strict outbound connection rules
2. **DNS Resolution Issues**: Corporate/hosting DNS may not resolve PhonePe domains
3. **Proxy/Load Balancer Interference**: Corporate proxies blocking API calls
4. **SSL/TLS Configuration**: Certificate issues on production server
5. **Hosting Provider Restrictions**: Some providers block certain external API calls

## Immediate Solutions

### 1. Test Connectivity on Production Server

Run these scripts on your production server to diagnose the exact issue:

```bash
# Upload and run the connectivity test
python manage.py shell -c "exec(open('test_simple_connectivity.py').read())"
```

### 2. Manual Server Testing

SSH into your production server and run:

```bash
# Test basic connectivity
curl -v https://api.phonepe.com
curl -v https://mercury-t2.phonepe.com

# Test with timeout
curl -m 60 -v https://api.phonepe.com/apis/hermes/pg/v1/pay

# Check DNS resolution
nslookup api.phonepe.com
dig api.phonepe.com

# Test from Python directly
python3 -c "
import requests
try:
    r = requests.get('https://api.phonepe.com', timeout=30)
    print(f'Success: {r.status_code}')
except Exception as e:
    print(f'Error: {e}')
"
```

### 3. Firewall Configuration

Ask your hosting provider to whitelist these domains and IP ranges:

**Domains to Whitelist:**
- api.phonepe.com
- mercury-t2.phonepe.com  
- api-preprod.phonepe.com (backup)

**Ports:**
- Outbound HTTPS (443)
- Outbound HTTP (80) for redirects

### 4. Environment-Specific Configuration

The updated code includes production-specific settings. Ensure your `.env` has:

```bash
PRODUCTION_SERVER=True
PHONEPE_TIMEOUT=90
PHONEPE_MAX_RETRIES=5
PHONEPE_SSL_VERIFY=True
```

## Updated Code Features

### Enhanced Connectivity
- Multiple fallback endpoints
- Progressive timeout increases
- Production-optimized connection pools
- Better error categorization

### Improved Error Handling
- Connection refused detection
- DNS resolution fallbacks
- SSL error recovery
- Proxy detection

### Debug Information
- Detailed error logging
- Network diagnostic info
- Admin-friendly error messages

## Hosting Provider Solutions

### Common Hosting Platforms

**1. AWS EC2/Lightsail:**
```bash
# Check security groups
aws ec2 describe-security-groups

# Ensure outbound HTTPS is allowed
# Default VPC usually allows all outbound traffic
```

**2. Google Cloud Platform:**
```bash
# Check firewall rules
gcloud compute firewall-rules list

# Create rule if needed
gcloud compute firewall-rules create allow-phonepe-outbound \
    --direction=EGRESS --action=ALLOW \
    --destination-ranges=0.0.0.0/0 --rules=tcp:443
```

**3. DigitalOcean:**
```bash
# Check if UFW is blocking
sudo ufw status
sudo ufw allow out 443
```

**4. Shared Hosting:**
- Contact support to whitelist PhonePe domains
- Ask for outbound HTTPS access confirmation
- Request proxy/firewall logs

## Alternative Solutions

### 1. Proxy Configuration
If your server requires a proxy:

```python
# Add to settings.py
PHONEPE_PROXY = {
    'http': 'http://proxy.company.com:8080',
    'https': 'https://proxy.company.com:8080'
}
```

### 2. IP Whitelisting
If domain whitelisting fails, get PhonePe IP ranges:

```bash
# Get PhonePe IPs
dig api.phonepe.com +short
nslookup api.phonepe.com
```

### 3. VPN/Tunnel Solution
For restricted environments:

```bash
# Use SSH tunnel
ssh -L 8443:api.phonepe.com:443 user@unrestricted-server

# Update code to use localhost:8443
```

## Testing & Verification

### 1. Step-by-Step Testing
```bash
# 1. Basic connectivity
telnet api.phonepe.com 443

# 2. HTTP test
curl -I https://api.phonepe.com

# 3. Full API test
curl -X POST https://api.phonepe.com/apis/hermes/pg/v1/pay \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# 4. Python requests test
python3 test_simple_connectivity.py
```

### 2. Monitor Logs
```bash
# Check system logs
sudo tail -f /var/log/syslog
sudo tail -f /var/log/nginx/error.log

# Check Django logs
tail -f logs/django.log
```

## Production Deployment Checklist

- [ ] Run connectivity tests on production server
- [ ] Verify outbound HTTPS (443) is allowed
- [ ] Whitelist PhonePe domains in firewall
- [ ] Check for corporate proxy settings
- [ ] Test DNS resolution for PhonePe domains
- [ ] Verify SSL certificate trust store
- [ ] Contact hosting provider if needed
- [ ] Test payment flow end-to-end
- [ ] Monitor error logs after deployment

## Contact Information

If connectivity issues persist:

1. **Hosting Provider**: Provide this document and test results
2. **PhonePe Support**: Report network connectivity issues
3. **Network Team**: Share firewall and proxy requirements

## Expected Timeline

- **Immediate**: Run diagnostic tests (15 minutes)
- **Quick Fix**: Firewall configuration (1-2 hours)
- **Provider Response**: 24-48 hours for hosting support
- **Complete Resolution**: 1-3 business days

## Success Indicators

✅ Connectivity tests pass
✅ Payment URLs are generated successfully  
✅ PhonePe redirects work properly
✅ Webhook callbacks are received
✅ Payment status updates correctly
