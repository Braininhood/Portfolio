import re
import bleach
from django.template.defaultfilters import striptags

def sanitize_html(html_content, allow_tags=None):
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Args:
        html_content (str): HTML content to sanitize
        allow_tags (list): List of allowed HTML tags, defaults to basic formatting tags
        
    Returns:
        str: Sanitized HTML
    """
    if allow_tags is None:
        allow_tags = ['p', 'br', 'strong', 'em', 'u', 'a']
    
    allowed_attributes = {
        'a': ['href', 'title', 'target'],
        '*': ['class']
    }
    
    # Bleach handles stripping of dangerous HTML tags and attributes
    return bleach.clean(
        html_content,
        tags=allow_tags,
        attributes=allowed_attributes,
        strip=True
    )

def sanitize_text(text):
    """
    Completely strip any HTML tags for plain text fields
    
    Args:
        text (str): Text that might contain HTML
        
    Returns:
        str: Plain text with HTML tags removed
    """
    if not text:
        return ""
    
    # First use bleach to handle potential XSS payloads
    cleaned = bleach.clean(text, tags=[], strip=True)
    # Then use striptags as a second layer of protection
    return striptags(cleaned)

def validate_image_file(image_file):
    """
    Validate image file type and size
    
    Args:
        image_file: UploadedFile object
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not image_file:
        return True, None
    
    # Check file type
    valid_mime_types = ['image/jpeg', 'image/png', 'image/jpg']
    if image_file.content_type not in valid_mime_types:
        return False, "Invalid file type. Only JPEG and PNG files are allowed."
    
    # Check file size (5MB max)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    if image_file.size > max_size:
        return False, "File size too large. Maximum allowed size is 5MB."
    
    return True, None

def validate_username(username):
    """
    Validate username format
    
    Args:
        username (str): Username to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check length
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    
    # Check for alphanumeric with underscores only
    pattern = re.compile(r'^[a-zA-Z0-9_]+$')
    if not pattern.match(username):
        return False, "Username can only contain letters, numbers, and underscores."
    
    return True, None

def detect_sql_injection(text):
    """
    Detect potential SQL injection attempts
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if potential SQL injection detected
    """
    if not text:
        return False
    
    # SQL injection pattern - now more lenient
    # Only detect clear SQL injection attempts with multiple SQL keywords
    pattern = re.compile(
        r'(\b(select|update|delete|insert|drop|alter)\b.*(from|table|where)\b.*(\bor\b|\band\b|--|;))', 
        re.IGNORECASE
    )
    
    return bool(pattern.search(text))

def detect_xss(text):
    """
    Detect potential XSS attempts
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if potential XSS detected
    """
    if not text:
        return False
    
    # XSS pattern - now more lenient
    # Only detect actual script tags and obvious event handlers
    pattern = re.compile(
        r'(<script.*>|<iframe.*src|javascript\s*:|on(click|load|error)\s*=)',
        re.IGNORECASE
    )
    
    return bool(pattern.search(text))

def escape_json_string(json_string):
    """
    Escape special characters in JSON string values
    
    Args:
        json_string (str): JSON string to escape
        
    Returns:
        str: Escaped JSON string
    """
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
    }
    
    for char, replacement in replacements.items():
        json_string = json_string.replace(char, replacement)
    
    return json_string

def get_nested_comments(comment, request):
    """
    Helper function to recursively get a comment and all its nested replies.
    Returns the comment data with nested replies structure.
    """
    # Get reactions for the comment
    comment_reactions = {}
    for reaction in comment.reactions.all():
        if reaction.emoji in comment_reactions:
            comment_reactions[reaction.emoji] += 1
        else:
            comment_reactions[reaction.emoji] = 1
    
    # Get user's reactions for the comment
    user_comment_reactions = []
    if request.user.is_authenticated:
        user_comment_reactions = list(comment.reactions.filter(
            user=request.user
        ).values_list('emoji', flat=True))
    
    # Get all direct replies to this comment
    replies = comment.replies.all()
    replies_data = []
    
    # Process each reply recursively to get their nested replies
    for reply in replies:
        reply_data = get_nested_comments(reply, request)
        replies_data.append(reply_data)
    
    # Return comment data with nested replies
    return {
        "id": comment.id,
        "user": comment.user.username,
        "content": comment.content,
        "timestamp": comment.timestamp.strftime("%b %d %Y, %I:%M %p"),
        "is_owner": comment.user == request.user if request.user.is_authenticated else False,
        "is_edited": comment.is_edited,
        "replies": replies_data,
        "reactions": comment_reactions,
        "user_reactions": user_comment_reactions
    } 