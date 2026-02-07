"""Serializers for the analytics app."""
from rest_framework import serializers
from .models import UsageMetric, QualityScore


class UsageMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageMetric
        fields = "__all__"


class QualityScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityScore
        fields = "__all__"


class FeedbackSerializer(serializers.Serializer):
    execution_id = serializers.UUIDField()
    score = serializers.FloatField(min_value=0, max_value=10)
    score_type = serializers.ChoiceField(
        choices=["relevance", "completeness", "accuracy", "user_satisfaction"]
    )
    feedback = serializers.CharField(required=False, allow_blank=True)
