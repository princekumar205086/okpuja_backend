from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files import File
from misc.models import Event
import os
from io import BytesIO
from PIL import Image
import requests
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Seed test data for Events'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing events before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            Event.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all existing events'))

        # Sample event data
        events_data = [
            {
                'title': 'Maha Shivaratri Celebration 2025',
                'description': '''Join us for the grand celebration of Maha Shivaratri at our temple. 
                Experience divine blessings with special pujas, devotional songs, and traditional ceremonies.
                
                Program includes:
                - Special Rudrabhishek Puja
                - Devotional songs and bhajans
                - Traditional dance performances
                - Prasadam distribution
                - Night-long celebrations
                
                All devotees are welcome to participate in this auspicious occasion.''',
                'event_date': timezone.now().date() + timedelta(days=30),
                'start_time': '06:00',
                'end_time': '23:59',
                'location': 'Main Temple Hall, OkPuja Temple Complex',
                'registration_link': 'https://okpuja.com/register/shivaratri-2025',
                'status': 'PUBLISHED',
                'is_featured': True,
            },
            {
                'title': 'Krishna Janmashtami Festival',
                'description': '''Celebrate the birth of Lord Krishna with joy and devotion.
                
                Special arrangements include:
                - Midnight Abhishek ceremony
                - Jhankis depicting Krishna's life
                - Dance performances by local artists
                - Special prasadam (Makhan Mishri)
                - Children's fancy dress competition
                - Cultural programs throughout the day
                
                Experience the divine joy of Krishna consciousness with your family.''',
                'event_date': timezone.now().date() + timedelta(days=60),
                'start_time': '05:00',
                'end_time': '01:00',
                'location': 'OkPuja Temple Complex',
                'registration_link': 'https://okpuja.com/register/janmashtami-2025',
                'status': 'PUBLISHED',
                'is_featured': True,
            }
        ]

        # Create sample image for events
        def create_sample_image(title, color=(255, 140, 0)):
            """Create a sample image for events"""
            img = Image.new('RGB', (800, 600), color=color)
            # You can add text or other elements to the image here
            return img

        created_events = []
        for i, event_data in enumerate(events_data):
            try:
                # Create sample image
                img = create_sample_image(event_data['title'])
                
                # Convert to bytes
                img_io = BytesIO()
                img.save(img_io, format='JPEG', quality=85)
                img_io.seek(0)
                
                # Create Django File
                image_file = File(img_io, name=f'event_{i+1}_sample.jpg')
                
                # Create event
                event = Event.objects.create(
                    title=event_data['title'],
                    description=event_data['description'],
                    event_date=event_data['event_date'],
                    start_time=event_data['start_time'],
                    end_time=event_data['end_time'],
                    location=event_data['location'],
                    registration_link=event_data['registration_link'],
                    status=event_data['status'],
                    is_featured=event_data['is_featured'],
                    original_image=image_file
                )
                
                created_events.append(event)
                self.stdout.write(
                    self.style.SUCCESS(f'Created event: {event.title}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating event {event_data["title"]}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(created_events)} events with sample images'
            )
        )
        
        # Display created events info
        for event in created_events:
            self.stdout.write(f'Event ID: {event.id}, Slug: {event.slug}')
