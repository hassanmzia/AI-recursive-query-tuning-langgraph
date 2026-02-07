"""Views for the analytics app."""
from django.db.models import Avg, Count, Sum, F
from django.db.models.functions import TruncDate, TruncHour
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from agents.models import WorkflowExecution
from conversations.models import Session, Message
from documents.models import Document
from .models import UsageMetric, QualityScore
from .serializers import UsageMetricSerializer, QualityScoreSerializer, FeedbackSerializer


class DashboardView(APIView):
    """Dashboard overview analytics."""

    def get(self, request):
        executions = WorkflowExecution.objects.all()
        sessions = Session.objects.all()
        documents = Document.objects.all()

        total_executions = executions.count()
        completed = executions.filter(status="completed").count()
        failed = executions.filter(status="failed").count()

        avg_duration = executions.filter(
            status="completed", duration_ms__isnull=False
        ).aggregate(avg=Avg("duration_ms"))["avg"]

        avg_quality = QualityScore.objects.aggregate(avg=Avg("score"))["avg"]

        return Response({
            "overview": {
                "total_executions": total_executions,
                "completed_executions": completed,
                "failed_executions": failed,
                "success_rate": round(completed / total_executions * 100, 1) if total_executions else 0,
                "average_duration_ms": round(avg_duration) if avg_duration else 0,
                "total_sessions": sessions.count(),
                "active_sessions": sessions.filter(is_active=True).count(),
                "total_documents": documents.count(),
                "indexed_documents": documents.filter(status="indexed").count(),
                "average_quality_score": round(avg_quality, 2) if avg_quality else None,
            },
            "recent_executions": list(
                executions.order_by("-created_at")[:10].values(
                    "id", "workflow_type", "status", "input_query",
                    "duration_ms", "created_at",
                )
            ),
            "workflow_distribution": list(
                executions.values("workflow_type").annotate(
                    count=Count("id")
                ).order_by("-count")
            ),
            "status_distribution": list(
                executions.values("status").annotate(
                    count=Count("id")
                ).order_by("-count")
            ),
        })


class ExecutionTimelineView(APIView):
    """Timeline of workflow executions."""

    def get(self, request):
        period = request.query_params.get("period", "day")

        trunc_fn = TruncHour if period == "hour" else TruncDate

        timeline = (
            WorkflowExecution.objects
            .filter(status="completed")
            .annotate(period=trunc_fn("created_at"))
            .values("period")
            .annotate(
                count=Count("id"),
                avg_duration=Avg("duration_ms"),
            )
            .order_by("period")
        )

        return Response({"timeline": list(timeline)})


class QualityScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of quality scores."""

    queryset = QualityScore.objects.all()
    serializer_class = QualityScoreSerializer


class SubmitFeedbackView(APIView):
    """Submit user feedback on an answer."""

    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        score = QualityScore.objects.create(
            workflow_execution_id=serializer.validated_data["execution_id"],
            score_type=serializer.validated_data["score_type"],
            score=serializer.validated_data["score"],
            feedback=serializer.validated_data.get("feedback", ""),
        )

        # Also record as a usage metric
        UsageMetric.objects.create(
            metric_name="user_feedback",
            metric_value=score.score,
            dimensions={
                "execution_id": str(score.workflow_execution_id),
                "score_type": score.score_type,
            },
        )

        return Response(
            QualityScoreSerializer(score).data,
            status=status.HTTP_201_CREATED,
        )
