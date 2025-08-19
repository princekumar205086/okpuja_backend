from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """Split a string by delimiter and return as list"""
    if value:
        return str(value).split(delimiter)
    return []

@register.filter
def first(value):
    """Get first item from a list or string"""
    if hasattr(value, '__iter__') and not isinstance(value, str):
        try:
            return value[0]
        except (IndexError, TypeError):
            return ''
    return value

@register.filter
def title_case(value):
    """Convert string to title case"""
    if value:
        return str(value).title()
    return value
