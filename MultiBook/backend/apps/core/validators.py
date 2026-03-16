"""
Custom validators.
"""
import re
from django.core.exceptions import ValidationError


def validate_uk_postcode(value):
    """
    Validate UK postcode format.
    Examples: SW1A 1AA, M1 1AA, B33 8TH, W1A 0AX
    """
    # UK postcode regex pattern
    pattern = r'^[A-Z]{1,2}[0-9R][0-9A-Z]?\s?[0-9][ABD-HJLNP-UW-Z]{2}$'
    
    if not re.match(pattern, value.upper()):
        raise ValidationError(f'{value} is not a valid UK postcode format.')
    
    return value.upper()


def validate_phone_uk(value):
    """
    Validate UK phone number format.
    Examples: 020 1234 5678, +44 20 1234 5678, 07700 900000
    """
    # Remove spaces and common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', value)
    
    # UK phone number patterns
    patterns = [
        r'^\+44[1-9]\d{8,9}$',  # International format
        r'^0[1-9]\d{8,9}$',      # National format
        r'^0[1-5]\d{9}$',        # Landline
        r'^07\d{9}$',            # Mobile
    ]
    
    if not any(re.match(p, cleaned) for p in patterns):
        raise ValidationError(f'{value} is not a valid UK phone number.')
    
    return value


def validate_radius_miles(value):
    """
    Validate radius in miles (should be positive and reasonable).
    UK uses miles, not kilometers.
    """
    if value <= 0:
        raise ValidationError('Radius must be greater than 0.')
    if value > 60:
        raise ValidationError('Radius cannot exceed 60 miles.')
    return value


# Keep old function name for backward compatibility
def validate_radius_km(value):
    """
    DEPRECATED: Use validate_radius_miles instead.
    This function now validates miles, not kilometers.
    Kept for backward compatibility.
    """
    return validate_radius_miles(value)
