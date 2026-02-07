"""URL configuration for the Recursive Query Tuning application."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health_check(request):
    return Response({
        "status": "healthy",
        "service": "recursive-query-tuning-backend",
        "version": "1.0.0",
    })


@api_view(["GET"])
def api_root(request):
    return Response({
        "service": "AI Recursive Query Tuning API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health/",
            "agents": "/api/agents/",
            "documents": "/api/documents/",
            "conversations": "/api/conversations/",
            "analytics": "/api/analytics/",
        },
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api_root),
    path("api/health/", health_check),
    path("api/agents/", include("agents.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/conversations/", include("conversations.urls")),
    path("api/analytics/", include("analytics.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
