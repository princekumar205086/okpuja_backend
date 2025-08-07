# Production Migration Fix Guide

## Issue
`django.db.utils.OperationalError: duplicate column name: google_meet_link`

This happens because there are conflicting migrations trying to add the same column twice.

## Solution Commands (Run on Production Server)

### Step 1: Check Current Migration Status
```bash
cd /opt/api.okpuja.com
python manage.py showmigrations astrology
```

### Step 2: Fake Apply the Problematic Migration
```bash
python manage.py migrate astrology 0003_add_google_meet_fields --fake
```

### Step 3: Apply All Remaining Migrations
```bash
python manage.py migrate
```

### Step 4: Verify Migration Status
```bash
python manage.py showmigrations astrology
```

### Step 5: Collect Static Files (if needed)
```bash
python manage.py collectstatic --noinput
```

## Expected Output

After Step 2, you should see:
```
Operations to perform:
  Target specific migration: 0003_add_google_meet_fields, from astrology
Running migrations:
  Rendering model states... DONE
  Unapplying astrology.0008_merge_20250807_1725... FAKED
```

After Step 3, you should see:
```
Operations to perform:
  Apply all migrations: accounts, admin, astrology, auth, blog, booking, cart, cms, contenttypes, db_manager, gallery, misc, otp_totp, payments, promo, puja, sessions, token_blacklist
Running migrations:
  Applying astrology.0008_merge_20250807_1725... OK
```

## What This Does

1. **--fake flag**: Marks the problematic migration as applied without actually executing it
2. This prevents Django from trying to add columns that already exist
3. The merge migration will then apply correctly
4. All other pending migrations will complete successfully

## Verification

After completing these steps, your astrology app migrations should show:
```
astrology
 [X] 0001_initial
 [X] 0002_remove_astrologyservice_image_and_more
 [X] 0003_alter_astrologyservice_image_card_url_and_more
 [X] 0004_astrologybooking_metadata
 [X] 0005_add_booking_ids_custom
 [X] 0006_add_google_meet_fields
 [X] 0007_add_google_meet_session_fields
 [X] 0003_add_google_meet_fields
 [X] 0008_merge_20250807_1725
```

All with `[X]` indicating they are applied successfully.

## Notes

- This is the same issue we resolved locally
- The --fake flag is safe to use for migrations that try to add existing columns
- Your production database schema will remain intact
- All admin booking endpoints will continue working correctly
