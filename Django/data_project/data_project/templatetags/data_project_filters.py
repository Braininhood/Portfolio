from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to access dictionary items by key.
    Usage: {{ dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key, '')  # Return empty string instead of None when key is missing 