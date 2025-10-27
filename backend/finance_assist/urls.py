"""
URL configuration for finance_assist project.
"""
from django.contrib import admin
from django.urls import path, include
from . import health_views

urlpatterns = [
    path('', health_views.root_view, name='root'),
    path('health/', health_views.health_check, name='health'),
    path('admin/', admin.site.urls),
    path('api/', include('chat.urls')),
    path('api/document-processing/', include('document_processing.urls')),
]
