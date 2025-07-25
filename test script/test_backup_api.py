#!/usr/bin/env python
"""
Test script for database backup and restore API endpoints
"""
import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@okpuja.com"
ADMIN_PASSWORD = "admin@123"

def get_admin_token():
    """Get admin JWT token"""
    login_url = f"{BASE_URL}/api/auth/login/"
    data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(login_url, json=data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access')
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_backup_config(token):
    """Test backup configuration endpoint"""
    print("\n🔧 Testing Backup Configuration...")
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get current config
    response = requests.get(f"{BASE_URL}/api/db-manager/config/", headers=headers)
    print(f"GET config: {response.status_code}")
    if response.status_code == 200:
        config = response.json()
        print(f"Current config: {json.dumps(config, indent=2)}")
    
    return response.status_code == 200

def test_create_backup(token):
    """Test backup creation endpoint"""
    print("\n💾 Testing Backup Creation...")
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "backup_type": "MANUAL",
        "storage_type": "LOCAL"
    }
    
    response = requests.post(f"{BASE_URL}/api/db-manager/backups/create_backup/", json=data, headers=headers)
    print(f"POST create_backup: {response.status_code}")
    if response.status_code in [200, 201]:
        backup = response.json()
        print(f"Backup created: {json.dumps(backup, indent=2)}")
        return backup.get('backup_id')
    else:
        print(f"Backup creation failed: {response.text}")
    
    return None

def test_list_backups(token):
    """Test backup listing endpoint"""
    print("\n📋 Testing Backup Listing...")
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(f"{BASE_URL}/api/db-manager/backups/", headers=headers)
    print(f"GET backups: {response.status_code}")
    if response.status_code == 200:
        backups_data = response.json()
        if isinstance(backups_data, dict) and 'results' in backups_data:
            backups = backups_data['results']
        else:
            backups = backups_data
        print(f"Found {len(backups)} backups")
        return backups
    
    return []

def test_auto_backup(token):
    """Test auto backup endpoint"""
    print("\n🤖 Testing Auto Backup...")
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.post(f"{BASE_URL}/api/db-manager/backups/auto_backup/", headers=headers)
    print(f"POST auto_backup: {response.status_code}")
    if response.status_code in [200, 201]:
        backup = response.json()
        print(f"Auto backup: {json.dumps(backup, indent=2)}")
    else:
        print(f"Auto backup response: {response.text}")

def main():
    print("🧪 Testing Database Backup & Restore API")
    print("=" * 50)
    
    # Get admin token
    print("🔑 Getting admin token...")
    token = get_admin_token()
    if not token:
        print("❌ Failed to get admin token. Make sure server is running and admin exists.")
        return
    
    print("✅ Admin token obtained")
    
    # Test endpoints
    try:
        test_backup_config(token)
        backup_id = test_create_backup(token)
        test_list_backups(token)
        test_auto_backup(token)
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    main()
