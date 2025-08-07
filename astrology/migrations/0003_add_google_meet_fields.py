# Generated migration for Google Meet link functionality

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrology', '0002_remove_astrologyservice_image_and_more'),  # Fixed dependency
    ]

    operations = [
        migrations.AddField(
            model_name='astrologybooking',
            name='google_meet_link',
            field=models.URLField(blank=True, help_text='Google Meet link for the astrology session', null=True),
        ),
        migrations.AddField(
            model_name='astrologybooking',
            name='is_session_scheduled',
            field=models.BooleanField(default=False, help_text='Whether admin has scheduled the session'),
        ),
        migrations.AddField(
            model_name='astrologybooking',
            name='session_notes',
            field=models.TextField(blank=True, help_text='Additional notes about the session', null=True),
        ),
    ]
