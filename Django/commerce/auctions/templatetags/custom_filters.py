from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply the value by the argument."""
    return float(value) * float(arg)

@register.filter
def truncate_username(username):
    if len(username) > 10:
        return f"{username[:10]}..."
    return username

@register.filter
def truncate_description(description):
    if len(description) > 25:
        return f"{description[:25]}..."
    return description 