from django import template
from core.html_utils import clean_html_text, format_description_for_display

register = template.Library()


@register.filter
def clean_html(value):
    """Clean HTML tags from text"""
    return clean_html_text(value)


@register.filter
def format_description(value, preserve_formatting=True):
    """Format description for display"""
    return format_description_for_display(value, preserve_formatting)
