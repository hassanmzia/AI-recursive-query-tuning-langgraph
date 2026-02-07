"""URL configuration for the agents app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"configs", views.AgentConfigViewSet, basename="agent-config")
router.register(r"executions", views.WorkflowExecutionViewSet, basename="workflow-execution")

urlpatterns = [
    path("", include(router.urls)),
    path("execute/", views.ExecuteQueryView.as_view(), name="execute-query"),
    path("visualize/", views.WorkflowVisualizationView.as_view(), name="workflow-visualize"),
    path("mcp/", views.MCPView.as_view(), name="mcp"),
    path("a2a/", views.A2AView.as_view(), name="a2a"),
]
