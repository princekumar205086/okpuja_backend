"""
Django Management Command to test API response format
"""
from django.core.management.base import BaseCommand
from booking.models import Booking
from booking.serializers import BookingSerializer
import json

class Command(BaseCommand):
    help = 'Test booking API response format'
    
    def add_arguments(self, parser):
        parser.add_argument('booking_id', type=str, help='Booking ID to test')
        
    def handle(self, *args, **options):
        booking_id = options['booking_id']
        
        try:
            booking = Booking.objects.get(book_id=booking_id)
            
            # Simulate API response
            serializer = BookingSerializer(booking)
            api_response = {
                "success": True,
                "data": serializer.data,
                "message": "Booking retrieved successfully"
            }
            
            self.stdout.write(
                self.style.SUCCESS('=== API RESPONSE FORMAT ===')
            )
            
            # Pretty print the JSON response
            formatted_json = json.dumps(api_response, indent=2, default=str)
            self.stdout.write(formatted_json)
            
            # Check payment details specifically
            if 'payment_details' in api_response['data']:
                payment_data = api_response['data']['payment_details']
                self.stdout.write(
                    self.style.SUCCESS('\n✅ PAYMENT DETAILS FOUND IN API RESPONSE:')
                )
                for key, value in payment_data.items():
                    self.stdout.write(f"   {key}: {value}")
            else:
                self.stdout.write(
                    self.style.ERROR('\n❌ PAYMENT DETAILS NOT FOUND IN API RESPONSE')
                )
                
        except Booking.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Booking {booking_id} not found')
            )
