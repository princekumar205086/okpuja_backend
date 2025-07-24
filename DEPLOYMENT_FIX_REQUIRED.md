# 🚨 Deployment Fix Required - Server Setup Missing

## Issue Summary
Your GitHub Actions deployment is failing because the production server hasn't been initialized properly. The errors show:

- ❌ Directory `/opt/backend.okpuja.com` doesn't exist
- ❌ Git repository not initialized  
- ❌ Python virtual environment missing
- ❌ Required packages not installed

## 🔧 IMMEDIATE SOLUTION

### 1. Manual Server Setup (Required First)

SSH into your server and run these commands:

```bash
ssh root@157.173.221.192

# Install system packages
apt update -y
apt install -y python3 python3-pip python3-venv python3-full git nginx supervisor curl

# Create app directory and clone repo
mkdir -p /opt/backend.okpuja.com
cd /opt/backend.okpuja.com
git clone https://github.com/princekumar205086/okpuja_backend.git .

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file (copy from your local version)
# Important: Copy your entire .env file content to the server

# Run Django setup
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Configure and start services (detailed in setup_server.sh)
```

### 2. Use the Complete Setup Script

I've created a complete setup script. Run it on your server:

```bash
# Upload and run the setup script
curl -O https://raw.githubusercontent.com/princekumar205086/okpuja_backend/main/setup_server.sh
chmod +x setup_server.sh
bash setup_server.sh
```

### 3. Configure GitHub Secrets

Add your SSH private key to GitHub:
- Repository Settings → Secrets → Actions
- Name: `VPS_SSH_KEY`
- Value: Your private SSH key content

## ✅ After Manual Setup

Once you complete the manual setup:
1. Your app will be live at `http://157.173.221.192`
2. Future GitHub pushes will auto-deploy
3. PhonePe payment gateway will be functional

## 🎯 Test Commands

```bash
# Basic connectivity
curl -I http://157.173.221.192/

# API test
curl http://157.173.221.192/api/

# PhonePe connectivity test
curl http://157.173.221.192/api/payments/payments/debug-connectivity/
```

The updated GitHub Actions workflow is already configured and will work perfectly after the initial server setup is complete.

**Next Step**: Run the manual server setup commands above, then push your code to trigger the automated deployment!
