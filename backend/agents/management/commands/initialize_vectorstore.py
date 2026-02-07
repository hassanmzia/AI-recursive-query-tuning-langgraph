"""Management command to initialize the ChromaDB vector store with research papers."""
import os
import zipfile
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Initialize ChromaDB vector store with research papers from the zip file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-indexing even if collection exists",
        )

    def handle(self, *args, **options):
        force = options.get("force", False)

        try:
            import chromadb

            client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=int(settings.CHROMA_PORT),
            )

            # Check if collection already has data
            try:
                collection = client.get_collection("Research_Papers")
                count = collection.count()
                if count > 0 and not force:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Vector store already initialized with {count} documents. "
                            "Use --force to re-index."
                        )
                    )
                    return
            except Exception:
                pass  # Collection doesn't exist yet

            # Find and extract the zip file
            zip_path = "/app/data/agentic_ai_research_papers.zip"
            extract_path = "/app/data/agentic_ai_research_papers/"

            if not os.path.exists(zip_path):
                self.stdout.write(
                    self.style.WARNING(
                        f"Research papers zip not found at {zip_path}. "
                        "Vector store will be empty until documents are uploaded."
                    )
                )
                return

            self.stdout.write("Extracting research papers...")
            os.makedirs(extract_path, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall("/app/data/")

            # Find the actual PDF directory
            pdf_dir = extract_path
            if not any(f.endswith(".pdf") for f in os.listdir(pdf_dir)):
                # Try subdirectory
                subdirs = [
                    d for d in os.listdir(pdf_dir)
                    if os.path.isdir(os.path.join(pdf_dir, d))
                ]
                if subdirs:
                    pdf_dir = os.path.join(pdf_dir, subdirs[0])

            pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
            self.stdout.write(f"Found {len(pdf_files)} PDF files")

            if not pdf_files:
                self.stdout.write(self.style.WARNING("No PDF files found"))
                return

            # Load and process PDFs
            from langchain_community.document_loaders import PyPDFDirectoryLoader
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from langchain_openai import OpenAIEmbeddings
            from langchain_chroma import Chroma

            self.stdout.write("Loading PDFs...")
            loader = PyPDFDirectoryLoader(path=pdf_dir)

            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                encoding_name="cl100k_base",
                chunk_size=1000,
                chunk_overlap=200,
            )

            chunks = loader.load_and_split(text_splitter)
            self.stdout.write(f"Created {len(chunks)} text chunks")

            # Create embeddings and store
            self.stdout.write("Creating embeddings and indexing...")
            embeddings = OpenAIEmbeddings(
                model=settings.OPENAI_EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                openai_api_base=settings.OPENAI_BASE_URL,
            )

            # Delete existing collection if force
            if force:
                try:
                    client.delete_collection("Research_Papers")
                    self.stdout.write("Deleted existing collection")
                except Exception:
                    pass

            vectorstore = Chroma.from_documents(
                chunks,
                embeddings,
                client=client,
                collection_name="Research_Papers",
            )

            count = client.get_collection("Research_Papers").count()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Vector store initialized with {count} document chunks "
                    f"from {len(pdf_files)} papers"
                )
            )

            # Also save document metadata to the DB
            from documents.models import Document
            for pdf_file in pdf_files:
                Document.objects.update_or_create(
                    title=pdf_file.replace(".pdf", "").replace("_", " "),
                    defaults={
                        "file_path": os.path.join(pdf_dir, pdf_file),
                        "document_type": "pdf",
                        "status": "indexed",
                        "chunk_count": len([c for c in chunks if pdf_file in getattr(c.metadata, "source", c.metadata.get("source", ""))]),
                    },
                )
            self.stdout.write(self.style.SUCCESS("Document metadata saved to database"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to initialize vector store: {e}"))
            logger.error(f"Vector store initialization failed: {e}", exc_info=True)
