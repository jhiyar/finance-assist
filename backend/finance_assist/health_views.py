from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import connection
import json

@csrf_exempt
@require_http_methods(["GET", "POST"])
def health_check(request):
    """Health check endpoint for AWS App Runner"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return JsonResponse({
        "status": "healthy",
        "service": "finance-assist-backend",
        "version": "1.0.0",
        "database": db_status
    })

@csrf_exempt
@require_http_methods(["GET"])
def root_view(request):
    """Root endpoint with basic app information"""
    return JsonResponse({
        "message": "Finance Assist Backend API",
        "version": "1.0.0",
        "endpoints": {
            "admin": "/admin/",
            "api": "/api/",
            "document_processing": "/api/document-processing/",
            "health": "/health/"
        },
        "status": "running"
    })
