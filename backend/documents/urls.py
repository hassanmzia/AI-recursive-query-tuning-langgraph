"""URL configuration for the documents app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"", views.DocumentViewSet, basename="document")

urlpatterns = [
    path("upload/", views.DocumentUploadView.as_view(), name="document-upload"),
    path("search/", views.DocumentSearchView.as_view(), name="document-search"),
    path("", include(router.urls)),
]
