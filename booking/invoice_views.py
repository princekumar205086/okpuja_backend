from django.http import HttpResponse
from django.template.loader import get_template
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from booking.models import Booking
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.utils import ImageReader
from io import BytesIO
import datetime
import requests
from urllib.parse import urlparse

def generate_invoice_pdf_data(booking):
    """Generate PDF invoice data for a booking (for email attachment)"""
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        textColor=colors.HexColor('#333333')
    )
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    # Try to add logo
    try:
        logo_url = "https://media.licdn.com/dms/image/v2/D4E16AQGoOTbMqP7mVA/profile-displaybackgroundimage-shrink_200_800/profile-displaybackgroundimage-shrink_200_800/0/1726774481871?e=2147483647&v=beta&t=7o61d-oh2xOsk-EpkSlkTt227BkOZk-4p4FXx0ZyRRA"
        response = requests.get(logo_url)
        logo_img = ImageReader(BytesIO(response.content))
        logo = Image(logo_img, width=180, height=60)
        elements.append(logo)
        elements.append(Spacer(1, 10))
    except Exception as e:
        # Fallback to text if logo can't be loaded
        elements.append(Paragraph("OKPUJA", title_style))
    
    # Invoice Header
    elements.append(Paragraph("INVOICE", title_style))
    elements.append(Spacer(1, 15))
    
    # Company Information
    company_info = [
        ["OkPuja - Your Spiritual Journey Partner", ""],
        ["Email: support@okpuja.com", f"Invoice Date: {datetime.datetime.now().strftime('%B %d, %Y')}"],
        ["Phone: +91-XXXXXXXXXX", f"Invoice #: INV-{booking.book_id}"],
        ["Website: www.okpuja.com", f"Booking ID: {booking.book_id}"]
    ]
    
    company_table = Table(company_info, colWidths=[3.5*inch, 3.5*inch])
    company_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#2c3e50')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(company_table)
    elements.append(Spacer(1, 20))
    
    # Customer Information
    customer_name = "Valued Customer"
    if booking.user:
        if hasattr(booking.user, 'first_name') and booking.user.first_name:
            first_name = booking.user.first_name
            last_name = getattr(booking.user, 'last_name', '') or ''
            customer_name = f"{first_name} {last_name}".strip()
        elif hasattr(booking.user, 'username') and booking.user.username:
            customer_name = booking.user.username
        elif hasattr(booking.user, 'email') and booking.user.email:
            customer_name = booking.user.email.split('@')[0].title()
    
    # Create two-column layout for From and Bill To
    from_to_data = [
        ["From:", "Bill To:"],
        ["OkPuja - Your Spiritual Journey Partner", f"Name: {customer_name}"],
        ["123 Spiritual Street, Varanasi", f"Email: {booking.user.email if booking.user else 'N/A'}"],
        ["Uttar Pradesh, 221001, India", f"Phone: {getattr(booking.user, 'phone', 'N/A') or 'N/A'}"],
        ["support@okpuja.com | +91-XXXXXXXXXX", ""]
    ]
    
    if booking.address:
        from_to_data.extend([
            ["", f"Address: {booking.address.address_line1}"],
            ["", f"{getattr(booking.address, 'address_line2', '') or ''}"],
            ["", f"{booking.address.city}, {booking.address.state}"],
            ["", f"Postal Code: {booking.address.postal_code}, {booking.address.country}"]
        ])
    
    from_to_table = Table(from_to_data, colWidths=[3.5*inch, 3.5*inch])
    from_to_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e9ecef')),
    ]))
    elements.append(from_to_table)
    elements.append(Spacer(1, 20))
    
    # Service Details
    elements.append(Paragraph("Service Details:", heading_style))
    
    service_data = [
        ['Description', 'Date & Time', 'Amount'],
    ]
    
    # Service row
    service_name = booking.cart.puja_service.title if booking.cart.puja_service else "Service"
    service_date = f"{booking.selected_date.strftime('%B %d, %Y')} at {booking.selected_time}"
    service_amount = f"₹{booking.total_amount}"
    
    service_data.append([service_name, service_date, service_amount])
    
    # Package details if available
    if booking.cart.package:
        package_desc = f"Package: {booking.cart.package.package_type} - {getattr(booking.cart.package, 'location', '')}"
        service_data.append([package_desc, "", ""])
    
    # Add totals
    subtotal = booking.total_amount
    tax = subtotal * 0.10  # 10% tax for example
    total = subtotal + tax
    
    service_data.extend([
        ['', '', ''],
        ['', 'Subtotal:', f"₹{subtotal}"],
        ['', 'Tax (10%):', f"₹{tax}"],
        ['', 'Total Amount:', f"₹{total}"]
    ])
    
    service_table = Table(service_data, colWidths=[3.5*inch, 2*inch, 1.5*inch])
    service_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('PADDING', (0, 0), (-1, 0), 8),
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -4), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -4), 10),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('PADDING', (0, 1), (-1, -1), 6),
        
        # Total rows
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -3), (-1, -3), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8f9fa')),
        
        # Grid
        ('GRID', (0, 0), (-1, -4), 0.5, colors.HexColor('#e9ecef')),
    ]))
    elements.append(service_table)
    elements.append(Spacer(1, 20))
    
    # Payment Information
    if hasattr(booking, 'payment_details') and booking.payment_details:
        elements.append(Paragraph("Payment Information:", heading_style))
        payment_details = booking.payment_details
        
        payment_data = [
            ["Transaction ID", "Status", "Payment Date", "Amount Paid"],
            [
                payment_details.get('transaction_id', 'N/A'),
                payment_details.get('status', 'N/A'),
                payment_details.get('payment_date', 'N/A'),
                f"₹{payment_details.get('amount', booking.total_amount)}"
            ]
        ]
        
        payment_table = Table(payment_data, colWidths=[1.75*inch, 1.75*inch, 1.75*inch, 1.75*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e9ecef')),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 20))
    
    # Terms and Conditions
    elements.append(Paragraph("Terms & Conditions:", heading_style))
    terms_data = [
        ["• This is a computer-generated invoice and does not require a physical signature."],
        ["• Payment must be made in full before the service date."],
        ["• Cancellation policy applies as per our terms of service."],
        ["• For any queries, please contact our customer support."],
        ["• Thank you for choosing OkPuja for your spiritual needs."]
    ]
    
    terms_table = Table(terms_data, colWidths=[7*inch])
    terms_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(terms_table)
    elements.append(Spacer(1, 30))
    
    # Footer
    footer_text = [
        "Thank you for choosing OkPuja!",
        "May divine blessings bring peace and prosperity to your life.",
        "www.okpuja.com | support@okpuja.com | +91-XXXXXXXXXX"
    ]
    
    for text in footer_text:
        elements.append(Paragraph(text, footer_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_invoice_pdf(request, book_id):
    """Generate and return PDF invoice for a booking (authenticated)"""
    try:
        # Get booking
        booking = get_object_or_404(Booking, book_id=book_id, user=request.user)
        
        # Generate PDF data
        pdf_data = generate_invoice_pdf_data(booking)
        
        # Create response
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="OkPuja-Invoice-{booking.book_id}.pdf"'
        
        return response
        
    except Exception as e:
        return HttpResponse(f"Error generating invoice: {str(e)}", status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def public_invoice_pdf(request, book_id):
    """Generate and return PDF invoice for a booking (public access for email links)"""
    try:
        # Get booking - no user restriction for public access
        booking = get_object_or_404(Booking, book_id=book_id)
        
        # Additional security: only allow if booking has payment details
        # This ensures only confirmed bookings can have public invoices
        if not hasattr(booking, 'payment_details') or not booking.payment_details:
            return HttpResponse("Invoice not available for this booking", status=404)
        
        # Generate PDF data
        pdf_data = generate_invoice_pdf_data(booking)
        
        # Create response
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="OkPuja-Invoice-{booking.book_id}.pdf"'
        
        return response
        
    except Exception as e:
        return HttpResponse(f"Error generating invoice: {str(e)}", status=500)