"""Models for document management."""
import uuid
from django.db import models


class Document(models.Model):
    """Represents an uploaded/indexed document."""

    STATUS_CHOICES = [
        ("uploaded", "Uploaded"),
        ("processing", "Processing"),
        ("indexed", "Indexed"),
        ("failed", "Failed"),
    ]

    TYPE_CHOICES = [
        ("pdf", "PDF"),
        ("docx", "DOCX"),
        ("txt", "Text"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    file_path = models.CharField(max_length=1000)
    file_upload = models.FileField(upload_to="uploads/documents/", null=True, blank=True)
    document_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="pdf")
    file_size = models.BigIntegerField(default=0)
    page_count = models.IntegerField(default=0)
    chunk_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="uploaded")
    collection_name = models.CharField(max_length=255, default="Research_Papers")
    metadata = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    indexed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title


class DocumentChunk(models.Model):
    """Represents a chunk of a processed document."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_index = models.IntegerField()
    content = models.TextField()
    page_number = models.IntegerField(default=0)
    token_count = models.IntegerField(default=0)
    embedding_id = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ["document", "chunk_index"]
        unique_together = ["document", "chunk_index"]

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"
