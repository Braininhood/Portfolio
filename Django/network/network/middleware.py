import re
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseBadRequest
from django.conf import settings

class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware to enhance security by:
    1. Adding security headers to responses
    2. Preventing common attack patterns in requests
    3. Blocking suspicious URLs and patterns
    """
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.async_mode = False
        
        # Compile regex patterns for better performance
        self.sql_injection_pattern = re.compile(
            r'(\b(select|update|delete|insert|drop|alter|create|truncate)\b.*(from|table|database|values)|\'|\"|--|#|\/\*|\*\/)', 
            re.IGNORECASE
        )
        self.xss_pattern = re.compile(
            r'(<script|<iframe|<object|<embed|javascript:|vbscript:|on\w+\s*=|\bdata:)',
            re.IGNORECASE
        )
        
    def process_request(self, request):
        """Check incoming requests for potential security threats"""
        # Skip checks for static and media files
        if request.path.startswith(settings.STATIC_URL) or request.path.startswith(settings.MEDIA_URL):
            return None
            
        # Check GET parameters for SQL injection and XSS attempts
        for key, value in request.GET.items():
            if isinstance(value, str):
                if self.sql_injection_pattern.search(value):
                    return HttpResponseBadRequest("Bad request: Invalid parameters")
                if self.xss_pattern.search(value):
                    return HttpResponseBadRequest("Bad request: Invalid parameters")
        
        # For POST, only check if it's a form submission (not JSON or file upload)
        if request.method == 'POST' and not request.content_type.startswith('application/json') and not request.content_type.startswith('multipart/form-data'):
            for key, value in request.POST.items():
                if isinstance(value, str):
                    if self.sql_injection_pattern.search(value):
                        return HttpResponseBadRequest("Bad request: Invalid input")
                    if self.xss_pattern.search(value):
                        return HttpResponseBadRequest("Bad request: Invalid input")
        
        return None
    
    def process_response(self, request, response):
        """Add security headers to all responses"""
        # Content Security Policy
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; img-src 'self' data: blob:; font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; connect-src 'self'"
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Control browser features
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        
        # Prevent clickjacking
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        # XSS Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response 