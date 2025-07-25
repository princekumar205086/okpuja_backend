#!/usr/bin/env python
"""
PhonePe V2 Deployment Script
Helps deploy the V2 implementation to production
"""

import subprocess
import os
import sys

def run_command(command, description):
    """Run a command and show the result"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False
    return True

def check_git_status():
    """Check git status"""
    print("📋 Checking Git Status")
    print("=" * 40)
    
    if not run_command("git status --porcelain", "Checking for changes"):
        return False
    
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print("📝 Files with changes:")
        for line in result.stdout.strip().split('\n'):
            print(f"   {line}")
    else:
        print("✅ No uncommitted changes")
    
    return True

def deploy_to_git():
    """Deploy changes to git"""
    print("\n🚀 Deploying V2 Implementation")
    print("=" * 40)
    
    # Add all changes
    if not run_command("git add .", "Adding files to git"):
        return False
    
    # Commit changes
    commit_message = "feat: PhonePe V2 API integration - Fix CONNECTION_REFUSED error"
    if not run_command(f'git commit -m "{commit_message}"', "Committing changes"):
        print("ℹ️ No new changes to commit (this is okay if already committed)")
    
    # Push to remote
    if not run_command("git push origin main", "Pushing to remote repository"):
        return False
    
    return True

def show_production_deployment_instructions():
    """Show instructions for production deployment"""
    print("\n🏭 Production Server Deployment Instructions")
    print("=" * 50)
    
    instructions = [
        "1. SSH into your production server",
        "2. Navigate to your Django project directory",
        "3. Pull the latest changes: git pull origin main", 
        "4. Restart your Django service:",
        "   - sudo systemctl restart gunicorn",
        "   - OR sudo systemctl restart uwsgi",
        "   - OR supervisorctl restart your-django-app",
        "5. Check logs: tail -f /var/log/django/error.log",
        "6. Test the V2 integration: python simple_v2_check.py"
    ]
    
    for instruction in instructions:
        print(f"   {instruction}")
    
    print("\n🧪 Verification Commands (run on production server):")
    print("   cd /path/to/your/django/project")
    print("   python simple_v2_check.py")
    print("   # Should show: 'V2 Integration is WORKING!'")

def show_files_being_deployed():
    """Show what files are being deployed"""
    print("\n📦 Files Being Deployed:")
    print("=" * 30)
    
    important_files = [
        "payment/gateways_v2.py - NEW V2 gateway implementation",
        "payment/views.py - Updated to use V2 gateway", 
        ".env - V2 credentials and settings",
        "okpuja_backend/settings.py - V2 configuration",
        "simple_v2_check.py - Verification script"
    ]
    
    for file in important_files:
        if os.path.exists(file.split(' - ')[0]):
            print(f"   ✅ {file}")
        else:
            print(f"   ⚠️ {file} (not found locally)")

def main():
    """Main deployment function"""
    print("🚀 PhonePe V2 Production Deployment")
    print("=" * 60)
    print("This script will help you deploy the V2 implementation to production")
    print()
    
    # Check current directory
    if not os.path.exists("manage.py"):
        print("❌ Error: Run this script from your Django project root directory")
        sys.exit(1)
    
    # Show files being deployed
    show_files_being_deployed()
    
    # Check git status
    if not check_git_status():
        print("❌ Git status check failed")
        return
    
    # Ask for confirmation
    print("\n🤔 Ready to deploy V2 implementation?")
    response = input("   Type 'yes' to continue: ").lower().strip()
    
    if response != 'yes':
        print("❌ Deployment cancelled")
        return
    
    # Deploy to git
    if deploy_to_git():
        print("\n✅ Successfully pushed to git repository!")
        show_production_deployment_instructions()
        
        print("\n🎉 NEXT STEPS:")
        print("=" * 60)
        print("1. ✅ Local V2 implementation: READY")
        print("2. ✅ Git repository: UPDATED") 
        print("3. 🔄 Production server: NEEDS UPDATE")
        print("4. 🧪 Testing: PENDING")
        print()
        print("Follow the production deployment instructions above to complete the deployment!")
        
    else:
        print("\n❌ Deployment failed. Please check the errors above.")

if __name__ == "__main__":
    main()
