# Legacy Payment App Cleanup Instructions

## 🎉 Your Payment System is Working Perfectly!

Your new `payments` app is fully functional and tested. The old `payment` app can now be safely removed.

## ✅ Verified Working Components:
- ✅ PhonePe V2 integration with your credentials
- ✅ Payment URL generation from UAT environment  
- ✅ Complete flow: Cart → Payment → Booking
- ✅ Payment-first approach implemented
- ✅ Booking auto-creation working
- ✅ Clean folder structure organized

## 🧹 Safe Cleanup Steps:

### Step 1: Update settings.py
Remove `'payment',` from INSTALLED_APPS and ensure `'payments',` is present:

```python
INSTALLED_APPS = [
    # ... other apps
    'accounts',
    'payments',  # ✅ Keep this (new clean app)
    # 'payment',  # ❌ Remove this line
    # ... other apps
]
```

### Step 2: Update main urls.py  
Remove old payment URLs and ensure new payments URLs are included:

```python
urlpatterns = [
    # ... other URLs
    path('api/v1/payments/', include('payments.urls')),  # ✅ Keep this
    # path('api/payment/', include('payment.urls')),     # ❌ Remove this
    # ... other URLs
]
```

### Step 3: Run migrations (if needed)
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Test the application
```bash
python manage.py runserver
```

### Step 5: Delete the legacy payment folder (FINAL STEP)
Only after confirming everything works:
```bash
# On Windows PowerShell:
Remove-Item -Recurse -Force payment/

# Or manually delete the payment/ folder
```

## ⚠️ Important Notes:
- **Backup created**: Legacy code is backed up in `backups/` folder
- **Test first**: Always test your application before final deletion
- **Production**: Update production settings when deploying

## 🎯 Your New Payment Structure:
```
okpuja_backend/
├── payments/          # ✅ New clean payments app
├── tests/            # ✅ All test scripts organized  
├── readme/           # ✅ Documentation
└── payment/          # ❌ Legacy (safe to delete)
```

## 🚀 Ready for Production!
Your PhonePe V2 integration is production-ready with both UAT and production credentials configured.
