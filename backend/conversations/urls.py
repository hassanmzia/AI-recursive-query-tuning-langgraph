"""URL configuration for the conversations app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"sessions", views.SessionViewSet, basename="session")
router.register(r"messages", views.MessageViewSet, basename="message")

urlpatterns = [
    path("", include(router.urls)),
]
