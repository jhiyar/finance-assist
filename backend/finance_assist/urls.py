"""
URL configuration for finance_assist project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('chat.urls')),
    path('api/document-processing/', include('document_processing.urls')),
]
