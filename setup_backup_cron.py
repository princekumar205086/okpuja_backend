#!/usr/bin/env python
"""
Setup script for automatic database backup using Windows Task Scheduler
"""
import os
import sys
import subprocess
from pathlib import Path

def setup_windows_task():
    """Setup Windows Task Scheduler for daily backup"""
    
    # Get project paths
    project_dir = Path(__file__).parent
    manage_py = project_dir / 'manage.py'
    python_exe = sys.executable
    
    # Task command
    task_command = f'"{python_exe}" "{manage_py}" auto_backup'
    
    # PowerShell command to create scheduled task
    powershell_script = f'''
$Action = New-ScheduledTaskAction -Execute '{python_exe}' -Argument '"{manage_py}" auto_backup' -WorkingDirectory '{project_dir}'
$Trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName "OkPuja_Auto_Backup" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Automatic database backup for OkPuja backend"

Write-Host "Scheduled task 'OkPuja_Auto_Backup' created successfully!"
Write-Host "The task will run daily at 2:00 AM"
Write-Host "You can view/modify it in Task Scheduler (taskschd.msc)"
'''
    
    try:
        # Run PowerShell command
        result = subprocess.run(
            ['powershell', '-Command', powershell_script],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode == 0:
            print("✅ Windows Task Scheduler setup completed!")
            print("📅 Auto backup will run daily at 2:00 AM")
            print("🔧 You can modify the schedule in Task Scheduler (Run: taskschd.msc)")
            return True
        else:
            print("❌ Failed to create scheduled task:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error setting up scheduled task: {e}")
        return False

def setup_manual_instructions():
    """Provide manual setup instructions"""
    project_dir = Path(__file__).parent
    manage_py = project_dir / 'manage.py'
    python_exe = sys.executable
    
    print("\n📋 Manual Setup Instructions:")
    print("=" * 50)
    print("1. Open Task Scheduler (Run: taskschd.msc)")
    print("2. Click 'Create Basic Task' in the right panel")
    print("3. Name: OkPuja_Auto_Backup")
    print("4. Trigger: Daily")
    print("5. Time: 2:00 AM (or your preferred time)")
    print("6. Action: Start a program")
    print(f"7. Program: {python_exe}")
    print(f"8. Arguments: \"{manage_py}\" auto_backup")
    print(f"9. Start in: {project_dir}")
    print("10. Finish the wizard")
    print("\n💡 Test the task by running:")
    print(f"   {python_exe} {manage_py} auto_backup")

if __name__ == "__main__":
    print("🔧 Setting up automatic database backup...")
    print("=" * 50)
    
    # Try automatic setup
    if not setup_windows_task():
        # Provide manual instructions if automatic setup fails
        setup_manual_instructions()
    
    print("\n📖 Additional Commands:")
    print("- Manual backup: python manage.py auto_backup --force")
    print("- Cleanup old backups: python manage.py cleanup_backups")
    print("- View backup status via Django admin or API endpoints")
