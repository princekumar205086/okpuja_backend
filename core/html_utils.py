"""
HTML utilities for cleaning text fields
"""
import re
from html import unescape
from django.utils.html import strip_tags


def clean_html_text(text):
    """
    Clean HTML content to plain text with proper formatting
    
    Args:
        text (str): Text potentially containing HTML
        
    Returns:
        str: Clean plain text with preserved formatting
    """
    if not text:
        return text
    
    # Convert HTML entities to actual characters
    text = unescape(text)
    
    # Replace common HTML tags with appropriate formatting
    replacements = {
        # Paragraphs and line breaks
        r'<p[^>]*>': '\n\n',
        r'</p>': '',
        r'<br\s*/?>' : '\n',
        r'<hr\s*/?>': '\n---\n',
        
        # Headers
        r'<h[1-6][^>]*>': '\n\n',
        r'</h[1-6]>': '\n',
        
        # Lists
        r'<ul[^>]*>': '\n',
        r'</ul>': '\n',
        r'<ol[^>]*>': '\n',
        r'</ol>': '\n',
        r'<li[^>]*>': '\n• ',
        r'</li>': '',
        
        # Emphasis
        r'<strong[^>]*>': '**',
        r'</strong>': '**',
        r'<b[^>]*>': '**',
        r'</b>': '**',
        r'<em[^>]*>': '*',
        r'</em>': '*',
        r'<i[^>]*>': '*',
        r'</i>': '*',
        
        # Divs and spans
        r'<div[^>]*>': '\n',
        r'</div>': '',
        r'<span[^>]*>': '',
        r'</span>': '',
        
        # Tables (basic)
        r'<table[^>]*>': '\n',
        r'</table>': '\n',
        r'<tr[^>]*>': '\n',
        r'</tr>': '',
        r'<td[^>]*>': ' | ',
        r'</td>': '',
        r'<th[^>]*>': ' | ',
        r'</th>': '',
    }
    
    # Apply replacements
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Strip remaining HTML tags
    text = strip_tags(text)
    
    # Clean up whitespace
    # Remove excessive line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace from lines
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Remove leading/trailing whitespace from entire text
    text = text.strip()
    
    return text


def format_description_for_display(text, preserve_formatting=True):
    """
    Format description text for display in templates
    
    Args:
        text (str): Description text
        preserve_formatting (bool): Whether to preserve line breaks for HTML display
        
    Returns:
        str: Formatted text
    """
    if not text:
        return text
    
    # Clean HTML first
    text = clean_html_text(text)
    
    if preserve_formatting:
        # Convert line breaks to HTML breaks for template display
        text = text.replace('\n', '<br>')
    
    return text
