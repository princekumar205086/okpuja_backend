from django import template
from core.html_utils import clean_html_text, format_description_for_display
import re

register = template.Library()


@register.filter
def clean_html(value):
    """Clean HTML tags from text"""
    return clean_html_text(value)


@register.filter
def format_description(value, preserve_formatting=True):
    """Format description for display"""
    return format_description_for_display(value, preserve_formatting)


@register.filter
def extract_name_from_email(email):
    """Extract name from email address"""
    if not email:
        return "User"
    
    # Get the part before @
    name_part = email.split('@')[0]
    
    # Replace common separators with spaces and capitalize
    name_part = re.sub(r'[._-]', ' ', name_part)
    name_part = ' '.join(word.capitalize() for word in name_part.split())
    
    return name_part if name_part else "User"
