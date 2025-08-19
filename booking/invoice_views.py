from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from booking.models import Booking
from xhtml2pdf import pisa
from io import BytesIO
import datetime
from django.conf import settings

def generate_invoice_html(booking):
    """Generate HTML invoice for a booking"""
    context = {
        'booking': booking,
        'now': timezone.now()
    }
    return render_to_string('invoices/professional_invoice.html', context)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_invoice_html_view(request, book_id):
    """Generate and return HTML invoice for a booking (authenticated)"""
    try:
        booking = get_object_or_404(Booking, book_id=book_id, user=request.user)
        context = {
            'booking': booking,
            'now': timezone.now()
        }
        return render(request, 'invoices/professional_invoice.html', context)
    except Exception as e:
        return HttpResponse(f"Error generating invoice: {str(e)}", status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def public_invoice_html_view(request, book_id):
    """Generate and return HTML invoice for a booking (public access)"""
    try:
        booking = get_object_or_404(Booking, book_id=book_id)
        context = {
            'booking': booking,
            'now': timezone.now()
        }
        return render(request, 'invoices/professional_invoice.html', context)
    except Exception as e:
        return HttpResponse(f"Error generating invoice: {str(e)}", status=500)

def generate_invoice_pdf_data(booking):
    """Generate PDF invoice data for a booking using HTML-to-PDF (for email attachment)"""
    import warnings
    import logging
    
    # Suppress warnings during PDF generation
    warnings.filterwarnings('ignore')
    logging.getLogger('xhtml2pdf').setLevel(logging.ERROR)
    logging.getLogger('reportlab').setLevel(logging.ERROR)
    
    try:
        # Generate HTML content using the same template as the web view
        context = {
            'booking': booking,
            'now': timezone.now()
        }
        html_content = render_to_string('invoices/professional_invoice.html', context)
        
        # Create simplified HTML for PDF (remove Google Fonts to avoid warnings)
        pdf_html = html_content.replace(
            "@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Playfair+Display:wght@400;600;700&display=swap');",
            ""
        ).replace(
            "font-family: 'Roboto', sans-serif;",
            "font-family: Arial, sans-serif;"
        ).replace(
            "font-family: 'Playfair Display', serif;",
            "font-family: Georgia, serif;"
        ).replace(
            '<style>',
            '''<style>
            @page {
                size: A4;
                margin: 2cm;
            }
            
            body {
                background-color: white !important;
                padding: 0;
                margin: 0;
                font-family: Arial, sans-serif;
            }
            
            .invoice-container {
                max-width: none;
                width: 100%;
                margin: 0;
                padding: 20px;
                box-shadow: none !important;
            }
            
            .watermark {
                opacity: 0.05 !important;
            }
            
            .logo {
                max-width: 120px;
            }
            
            '''
        )
        
        # Create PDF from HTML using xhtml2pdf with suppressed output
        pdf_buffer = BytesIO()
        
        # Redirect stderr to suppress warnings
        import sys
        import os
        old_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        
        try:
            pisa_status = pisa.CreatePDF(pdf_html, dest=pdf_buffer)
        finally:
            sys.stderr.close()
            sys.stderr = old_stderr
        
        if pisa_status.err:
            raise Exception(f"PDF generation error: {pisa_status.err}")
        
        pdf_data = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        return pdf_data
    except Exception as e:
        # Fallback to a simple error PDF if HTML-to-PDF fails
        buffer = BytesIO()
        from reportlab.pdfgen import canvas
        try:
            p = canvas.Canvas(buffer)
            p.drawString(100, 750, f"Invoice - {booking.book_id}")
            p.drawString(100, 730, f"Error: {str(e)}")
            p.drawString(100, 710, f"Booking ID: {booking.book_id}")
            p.drawString(100, 690, f"Amount: ₹{booking.total_amount}")
            if booking.cart and booking.cart.puja_service:
                p.drawString(100, 670, f"Service: {booking.cart.puja_service.title}")
            p.drawString(100, 650, f"Date: {booking.selected_date}")
            p.showPage()
            p.save()
        except:
            p = canvas.Canvas(buffer)
            p.drawString(100, 750, f"OkPuja Invoice - {booking.book_id}")
            p.drawString(100, 730, f"Total: ₹{booking.total_amount}")
            p.showPage()
            p.save()
        
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_invoice_pdf(request, book_id):
    """Generate and return PDF invoice for a booking (authenticated)"""
    try:
        booking = get_object_or_404(Booking, book_id=book_id, user=request.user)
        pdf_data = generate_invoice_pdf_data(booking)
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="OkPuja-Invoice-{booking.book_id}.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f"Error generating invoice: {str(e)}", status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def public_invoice_pdf(request, book_id):
    """Generate and return PDF invoice for a booking (public access)"""
    try:
        booking = get_object_or_404(Booking, book_id=book_id)
        pdf_data = generate_invoice_pdf_data(booking)
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="OkPuja-Invoice-{booking.book_id}.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f"Error generating invoice: {str(e)}", status=500)
