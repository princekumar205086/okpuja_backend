# Generated migration for Google Meet link functionality

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrology', '0005_add_booking_ids_custom'),
    ]

    operations = [
        migrations.AddField(
            model_name='astrologybooking',
            name='google_meet_link',
            field=models.URLField(blank=True, help_text='Google Meet link for the astrology session', null=True, verbose_name='Google Meet Link'),
        ),
        migrations.AddField(
            model_name='astrologybooking',
            name='is_session_scheduled',
            field=models.BooleanField(default=False, help_text='Whether the session has been scheduled', verbose_name='Session Scheduled'),
        ),
        migrations.AddField(
            model_name='astrologybooking',
            name='session_notes',
            field=models.TextField(blank=True, help_text='Notes about the astrology session', null=True, verbose_name='Session Notes'),
        ),
    ]
