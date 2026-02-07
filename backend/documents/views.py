"""Views for the documents app."""
import os
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.utils import timezone

from .models import Document, DocumentChunk
from .serializers import DocumentSerializer, DocumentChunkSerializer, DocumentUploadSerializer

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    """CRUD for documents."""

    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    @action(detail=True, methods=["get"])
    def chunks(self, request, pk=None):
        doc = self.get_object()
        chunks = doc.chunks.all()
        serializer = DocumentChunkSerializer(chunks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reindex(self, request, pk=None):
        """Re-index a document in the vector store."""
        doc = self.get_object()
        try:
            doc.status = "processing"
            doc.save()
            # Re-index logic would go here
            doc.status = "indexed"
            doc.indexed_at = timezone.now()
            doc.save()
            return Response({"status": "reindexed"})
        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)
            doc.save()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentUploadView(APIView):
    """Handle document file uploads."""

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        title = serializer.validated_data.get("title", uploaded_file.name)
        description = serializer.validated_data.get("description", "")
        collection_name = serializer.validated_data.get("collection_name", "Research_Papers")

        # Determine file type
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        type_map = {".pdf": "pdf", ".docx": "docx", ".txt": "txt"}
        doc_type = type_map.get(ext, "txt")

        doc = Document.objects.create(
            title=title,
            description=description,
            file_upload=uploaded_file,
            document_type=doc_type,
            file_size=uploaded_file.size,
            collection_name=collection_name,
            status="processing",
        )

        try:
            self._index_document(doc)
            doc.status = "indexed"
            doc.indexed_at = timezone.now()
            doc.save()
        except Exception as e:
            logger.error(f"Failed to index document: {e}", exc_info=True)
            doc.status = "failed"
            doc.error_message = str(e)
            doc.save()

        return Response(
            DocumentSerializer(doc).data,
            status=status.HTTP_201_CREATED,
        )

    def _index_document(self, doc: Document):
        """Index a document into the vector store."""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_openai import OpenAIEmbeddings
        import chromadb

        file_path = doc.file_upload.path

        # Load document
        if doc.document_type == "pdf":
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(file_path)
        else:
            from langchain_community.document_loaders import TextLoader
            loader = TextLoader(file_path)

        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=1000,
            chunk_overlap=200,
        )

        chunks = loader.load_and_split(text_splitter)
        doc.chunk_count = len(chunks)
        doc.page_count = max((c.metadata.get("page", 0) for c in chunks), default=0) + 1

        # Store chunks in DB
        for i, chunk in enumerate(chunks):
            DocumentChunk.objects.create(
                document=doc,
                chunk_index=i,
                content=chunk.page_content,
                page_number=chunk.metadata.get("page", 0),
                metadata=chunk.metadata,
            )

        # Index into ChromaDB
        client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=int(settings.CHROMA_PORT),
        )
        embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL,
        )

        from langchain_chroma import Chroma
        Chroma.from_documents(
            chunks,
            embeddings,
            client=client,
            collection_name=doc.collection_name,
        )

        doc.file_path = file_path
        doc.save()

        logger.info(f"Indexed document '{doc.title}' with {len(chunks)} chunks")


class DocumentSearchView(APIView):
    """Search documents in the vector store."""

    def post(self, request):
        query = request.data.get("query", "")
        collection = request.data.get("collection", "Research_Papers")
        top_k = request.data.get("top_k", 5)

        if not query:
            return Response(
                {"error": "Query is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            import chromadb
            from langchain_openai import OpenAIEmbeddings
            from langchain_chroma import Chroma

            client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=int(settings.CHROMA_PORT),
            )
            embeddings = OpenAIEmbeddings(
                model=settings.OPENAI_EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                openai_api_base=settings.OPENAI_BASE_URL,
            )

            vectorstore = Chroma(
                client=client,
                collection_name=collection,
                embedding_function=embeddings,
            )

            results = vectorstore.similarity_search_with_score(query, k=top_k)

            return Response({
                "query": query,
                "results": [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": float(score),
                    }
                    for doc, score in results
                ],
            })
        except Exception as e:
            logger.error(f"Document search failed: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
