"""Models for analytics and monitoring."""
import uuid
from django.db import models


class UsageMetric(models.Model):
    """Tracks system usage metrics."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    dimensions = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["metric_name", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value}"


class QualityScore(models.Model):
    """Tracks answer quality scores over time."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_execution_id = models.UUIDField()
    score_type = models.CharField(
        max_length=50,
        choices=[
            ("relevance", "Relevance"),
            ("completeness", "Completeness"),
            ("accuracy", "Accuracy"),
            ("user_satisfaction", "User Satisfaction"),
        ],
    )
    score = models.FloatField()
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.score_type}: {self.score}"
