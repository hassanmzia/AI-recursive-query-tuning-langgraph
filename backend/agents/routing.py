"""WebSocket URL routing for the agents app."""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/workflow/(?P<session_id>\w+)/$", consumers.WorkflowStreamConsumer.as_asgi()),
    re_path(r"ws/workflow/$", consumers.WorkflowStreamConsumer.as_asgi()),
]
