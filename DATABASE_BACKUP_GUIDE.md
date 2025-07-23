# Database Backup & Restore System

## Overview
A comprehensive database backup and restore system for OkPuja backend with automatic daily backups, multiple storage options, and admin-only access controls.

## Features

### ✅ **Fixed Issues**
- **Database exclusion from Git**: Updated `.gitignore` to properly exclude `db.sqlite3` and backup files
- **Admin-only access**: All backup operations require admin privileges
- **Automatic daily backups**: Configurable auto-backup with retention policies
- **Multiple storage options**: Local, System path, and Google Drive (future)
- **Complete API documentation**: All endpoints documented in Swagger

### 🔧 **Core Functionality**

#### 1. **Backup Management**
- **Manual Backups**: Create backups on-demand
- **Automatic Backups**: Daily scheduled backups
- **Retention Policy**: Automatically delete old backups
- **File Compression**: Backups stored as ZIP files with metadata

#### 2. **Storage Options**
- **LOCAL**: Store in project directory (`backups/` folder)
- **SYSTEM**: Store in custom system path
- **GDRIVE**: Google Drive integration (future enhancement)

#### 3. **Restore Operations**
- **Full Database Restore**: Complete database replacement
- **Media Files Restore**: Restore uploaded files
- **Backup Validation**: Verify backup integrity before restore

## API Endpoints

### 🔐 Admin-Only Endpoints

All endpoints require admin authentication (`Authorization: Bearer <admin_jwt_token>`)

#### **Backup Configuration**
```
GET    /api/db-manager/config/          # Get backup configuration
PUT    /api/db-manager/config/1/        # Update backup configuration
```

#### **Backup Management**
```
GET    /api/db-manager/backups/         # List all backups
POST   /api/db-manager/backups/create_backup/  # Create manual backup
POST   /api/db-manager/backups/auto_backup/    # Create auto backup
GET    /api/db-manager/backups/{id}/download/  # Download backup file
DELETE /api/db-manager/backups/{id}/delete_backup/  # Delete backup
```

#### **Restore Operations**
```
GET    /api/db-manager/restore-logs/    # List restore history
POST   /api/db-manager/restore-logs/restore_backup/  # Restore from backup
```

## Usage Examples

### 1. **Create Manual Backup**
```bash
POST /api/db-manager/backups/create_backup/
Content-Type: application/json
Authorization: Bearer <admin_token>

{
    "backup_type": "MANUAL",
    "storage_type": "LOCAL",
    "custom_path": "/optional/custom/path"
}
```

### 2. **Configure Auto Backup**
```bash
PUT /api/db-manager/config/1/
Content-Type: application/json
Authorization: Bearer <admin_token>

{
    "storage_type": "LOCAL",
    "storage_path": "backups/",
    "auto_backup_enabled": true,
    "backup_retention_days": 7,
    "max_backup_files": 10
}
```

### 3. **Restore Database**
```bash
POST /api/db-manager/restore-logs/restore_backup/
Content-Type: application/json
Authorization: Bearer <admin_token>

{
    "backup_id": "backup_20250724_143022_a1b2c3d4",
    "confirm": true
}
```

## Management Commands

### **Manual Operations**
```bash
# Create manual backup
python manage.py auto_backup --force

# Clean up old backups
python manage.py cleanup_backups
```

### **Automated Setup**
```bash
# Setup Windows scheduled task for daily backups
python setup_backup_cron.py
```

## Configuration Options

### **Environment Variables** (add to `.env`)
```env
# Database Backup Configuration
DB_BACKUP_STORAGE_TYPE=LOCAL
DB_BACKUP_PATH=backups/
DB_BACKUP_RETENTION_DAYS=7
DB_BACKUP_MAX_FILES=10
DB_BACKUP_AUTO_ENABLED=True
```

### **Storage Types**
1. **LOCAL**: `backups/` folder in project directory
2. **SYSTEM**: Custom system path (configurable)
3. **GDRIVE**: Google Drive (future implementation)

## Backup File Structure

```
okpuja_backup_20250724_143022.zip
├── database.sqlite3           # Main database
├── media/                     # Media files (if any)
│   ├── uploads/
│   └── images/
└── backup_metadata.json       # Backup information
```

### **Metadata Example**
```json
{
    "backup_date": "2025-07-24T14:30:22.123456",
    "django_version": "5.2",
    "database_engine": "django.db.backends.sqlite3",
    "database_name": "/path/to/db.sqlite3",
    "apps": ["accounts", "puja", "astrology", ...],
    "backup_version": "1.0"
}
```

## Security Features

### **Admin-Only Access**
- All backup operations require admin role
- JWT token validation on every request
- Permission class: `IsAdminUser`

### **File Protection**
- Backup files excluded from version control
- Secure file download with authentication
- Temporary file cleanup after operations

## Installation & Setup

### **1. Add to Django Settings**
```python
INSTALLED_APPS = [
    # ... existing apps
    'db_manager',  # Add this line
]
```

### **2. Run Migrations**
```bash
python manage.py makemigrations db_manager
python manage.py migrate
```

### **3. Create Backup Directory**
```bash
mkdir backups
```

### **4. Setup Auto Backup (Windows)**
```bash
python setup_backup_cron.py
```

### **5. Test System**
```bash
# Test manual backup
python manage.py auto_backup --force

# Check admin interface
# Navigate to /admin/ and check "Database Manager" section
```

## Admin Interface

### **Django Admin Integration**
- **Backup Configurations**: Manage backup settings
- **Database Backups**: View, download, and delete backups
- **Restore Logs**: Track all restore operations

### **Admin Features**
- Download links for completed backups
- File size display in human-readable format
- Status tracking and error logging
- Bulk operations and filtering

## Monitoring & Logging

### **Backup Status Tracking**
- `PENDING`: Backup initiated
- `RUNNING`: Backup in progress
- `COMPLETED`: Backup successful
- `FAILED`: Backup failed (check error_message)
- `DELETED`: Backup file removed

### **Restore Status Tracking**
- `PENDING`: Restore initiated
- `RUNNING`: Restore in progress
- `COMPLETED`: Restore successful
- `FAILED`: Restore failed (check error_message)

## Troubleshooting

### **Common Issues**

#### 1. **Permission Denied**
- Ensure user has admin role
- Check JWT token validity
- Verify `IsAdminUser` permission

#### 2. **Backup File Not Found**
- Check storage path configuration
- Verify file wasn't deleted manually
- Check disk space availability

#### 3. **Restore Failed**
- Ensure backup file is valid ZIP
- Check database file permissions
- Verify backup is not corrupted

#### 4. **Auto Backup Not Running**
- Check scheduled task configuration
- Verify task scheduler service is running
- Check Django settings for auto backup enabled

### **Log Locations**
- Django logs: Check `error_message` field in admin
- System logs: Windows Event Viewer for scheduled tasks
- Manual testing: Command line output

## Future Enhancements

### **Planned Features**
1. **Google Drive Integration**: Cloud storage option
2. **Incremental Backups**: Save only changes since last backup
3. **Email Notifications**: Backup success/failure alerts
4. **Backup Encryption**: Password-protected backup files
5. **Multiple Database Support**: Backup additional databases
6. **Backup Verification**: Automatic integrity checks

### **API Improvements**
1. **Progress Tracking**: Real-time backup/restore progress
2. **Backup Scheduling**: Custom schedule configuration
3. **Backup Comparison**: Compare backup contents
4. **Selective Restore**: Restore specific tables/data

## Best Practices

### **Backup Strategy**
1. **Regular Testing**: Periodically test restore operations
2. **Multiple Locations**: Store backups in different locations
3. **Retention Policy**: Balance storage space vs. backup history
4. **Monitoring**: Regularly check backup status

### **Security Guidelines**
1. **Admin Access Only**: Never expose backup endpoints publicly
2. **Secure Storage**: Protect backup file access
3. **Audit Trail**: Monitor backup/restore operations
4. **Recovery Plan**: Document restore procedures

## Support

For issues or questions:
1. Check Django admin for error messages
2. Review backup logs in admin interface
3. Test with manual backup commands
4. Verify admin permissions and authentication

---

## Quick Reference

### **Essential Commands**
```bash
# Manual backup
python manage.py auto_backup --force

# Setup automation
python setup_backup_cron.py

# Clean old backups
python manage.py cleanup_backups

# Check migrations
python manage.py makemigrations db_manager
python manage.py migrate
```

### **Key API Endpoints**
- `POST /api/db-manager/backups/create_backup/` - Create backup
- `GET /api/db-manager/backups/` - List backups
- `POST /api/db-manager/restore-logs/restore_backup/` - Restore
- `GET /api/db-manager/config/` - View configuration

### **Admin URLs**
- `/admin/db_manager/backupconfig/` - Backup settings
- `/admin/db_manager/databasebackup/` - Backup management
- `/admin/db_manager/restorelog/` - Restore history
