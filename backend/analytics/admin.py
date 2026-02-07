from django.contrib import admin
from .models import UsageMetric, QualityScore


@admin.register(UsageMetric)
class UsageMetricAdmin(admin.ModelAdmin):
    list_display = ["metric_name", "metric_value", "timestamp"]
    list_filter = ["metric_name"]


@admin.register(QualityScore)
class QualityScoreAdmin(admin.ModelAdmin):
    list_display = ["score_type", "score", "workflow_execution_id", "created_at"]
    list_filter = ["score_type"]
