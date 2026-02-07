from django.contrib import admin
from .models import Session, Message, QueryRefinement


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "is_active", "created_at", "updated_at"]
    list_filter = ["is_active"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["role", "content", "session", "created_at"]
    list_filter = ["role"]

    def content(self, obj):
        return obj.content[:80]


@admin.register(QueryRefinement)
class QueryRefinementAdmin(admin.ModelAdmin):
    list_display = ["session", "iteration", "original_query", "refined_query"]
