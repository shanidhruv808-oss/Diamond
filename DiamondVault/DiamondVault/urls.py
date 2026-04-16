"""
URL configuration for DiamondVault project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

# Custom admin error handler
@login_required
def admin_error_view(request):
    """Custom error page for non-staff users trying to access admin"""
    return render(request, 'admin_error.html', {
        'username': request.user.username,
        'is_staff': request.user.is_staff
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('auction.urls')),
    path('admin-denied/', admin_error_view, name='admin_denied'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)