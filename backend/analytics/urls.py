"""URL configuration for the analytics app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"scores", views.QualityScoreViewSet, basename="quality-score")

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="analytics-dashboard"),
    path("timeline/", views.ExecutionTimelineView.as_view(), name="execution-timeline"),
    path("feedback/", views.SubmitFeedbackView.as_view(), name="submit-feedback"),
    path("", include(router.urls)),
]
