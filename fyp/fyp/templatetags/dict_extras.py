from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    try:
        if isinstance(dictionary, dict):
            return dictionary.get(key, key)
        return key
    except Exception:
        return key