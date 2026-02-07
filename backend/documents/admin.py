from django.contrib import admin
from .models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "document_type", "status", "chunk_count", "uploaded_at"]
    list_filter = ["status", "document_type"]
    search_fields = ["title", "description"]


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ["document", "chunk_index", "page_number", "token_count"]
    list_filter = ["document"]
