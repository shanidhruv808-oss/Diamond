from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseRedirect

class AdminAccessMiddleware:
    """
    Middleware to prevent non-staff users from accessing admin panel
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check admin access AFTER processing the request
        # This allows Django to handle authentication first
        if request.path.startswith('/admin/') and request.path != '/admin-login/':
            if request.user.is_authenticated and not request.user.is_staff:
                messages.error(request, "Access denied. You need admin privileges to access this page.")
                return HttpResponseRedirect('/admin-login/')
        
        return response
