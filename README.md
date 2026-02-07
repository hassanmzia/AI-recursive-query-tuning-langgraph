# AI Recursive Query Tuning — LangGraph Multi-Agent System

A production-grade AI-powered recursive query and answer tuning application built with **LangGraph**, featuring an **Adaptive ReAct QA workflow**, **multi-agent orchestration** with critique-revision loops, **MCP/A2A protocol** integrations, and full-stack observability via **LangSmith** and **Langfuse**.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [System Architecture Diagram](#system-architecture-diagram)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Port Assignments](#port-assignments)
- [API Reference](#api-reference)
- [LangGraph Workflow Detail](#langgraph-workflow-detail)
- [Multi-Agent Orchestration](#multi-agent-orchestration)
- [Document Processing Pipeline](#document-processing-pipeline)
- [Frontend Pages](#frontend-pages)
- [Database Schema](#database-schema)
- [Observability & Monitoring](#observability--monitoring)
- [Protocol Integrations](#protocol-integrations)
- [Key Architecture Decisions](#key-architecture-decisions)
- [Development Guide](#development-guide)
- [Troubleshooting](#troubleshooting)
- [Documentation Artifacts](#documentation-artifacts)

---

## Architecture Overview

```
                          ┌───────────────────────┐
                          │     User / Browser     │
                          └───────────┬───────────┘
                                      │ HTTP / WebSocket
                          ┌───────────▼───────────┐
                          │   React 19 Frontend    │
                          │   Nginx · Port 3082    │
                          │  TypeScript · Zustand   │
                          └───────────┬───────────┘
                                      │ REST (Axios) + WS
                          ┌───────────▼───────────┐
                          │  Node.js API Gateway   │
                          │  Express · Port 3083   │
                          │  Proxy · Rate Limit    │
                          └───────────┬───────────┘
                                      │ HTTP Proxy (body re-serialization)
                          ┌───────────▼───────────┐
                          │   Django 5 Backend     │
                          │   DRF · Port 8043      │
                          │  LangGraph · LangChain │
                          ├───────┬───────┬────────┤
                          │agents │docs   │convs   │
                          │       │       │analytics│
                          └──┬────┴──┬────┴──┬─────┘
                             │       │       │
                 ┌───────────┤       │       ├──────────────┐
                 │           │       │       │              │
          ┌──────▼──────┐ ┌──▼──────▼──┐ ┌──▼──────┐ ┌─────▼─────┐
          │ PostgreSQL   │ │  ChromaDB   │ │  Redis   │ │ Langfuse  │
          │ 16-alpine    │ │  0.6.3      │ │ 7-alpine │ │ v2        │
          │ Port 5532    │ │  Port 8142  │ │ Port 6478│ │ Port 3084 │
          └──────────────┘ └─────────────┘ └──────────┘ └───────────┘
```

All 7 services run as Docker Compose containers on an isolated bridge network (`rqt-network`), using non-default ports to avoid conflicts with existing services on the host.

---

## System Architecture Diagram

For detailed visual diagrams, see the `/docs` directory:

| File | Description |
|------|-------------|
| [`docs/architecture.drawio`](docs/architecture.drawio) | Editable draw.io technical architecture diagram (open in [app.diagrams.net](https://app.diagrams.net)) |
| [`docs/Technical_Architecture.pptx`](docs/Technical_Architecture.pptx) | 6-slide PowerPoint presentation covering all architecture layers |

---

## Features

### Core AI Workflows

#### Adaptive ReAct QA Workflow (LangGraph StateGraph)
The primary query execution engine implements a recursive retrieval-augmented generation pattern:

- **generate_query_or_respond** — Entry point: decides whether to answer directly or invoke RAG retrieval
- **retrieve** (ToolNode) — Fetches the top-k most relevant document chunks from ChromaDB vector store
- **grade_documents** — Binary relevance evaluation (`relevant` / `not_relevant`) of each retrieved chunk
- **rewrite_question** — Semantically refines the query when retrieved documents are not relevant
- **generate_answer** — Synthesizes the final answer from relevant context (max 3 sentences)

The workflow loops recursively: if documents are not relevant, the question is rewritten and retrieval is attempted again, up to a configurable iteration limit.

#### Multi-Agent Orchestration
A coordinated team of 5 specialized agents with a critique-revision quality loop:

| Agent | Role |
|-------|------|
| **Research Agent** | Searches and analyzes research paper content via vector store |
| **QA Specialist** | Synthesizes research findings into clear, structured answers |
| **Critique Agent** | Evaluates answer quality on a 1-10 scale with detailed feedback |
| **Revision Agent** | Improves the answer based on critique feedback |
| **Summarizer** | Creates a concise final summary of the approved answer |

The critique-revision loop continues until the quality score meets the threshold or max iterations are reached.

### Application Features

- **Real-time WebSocket streaming** of workflow execution progress
- **Document management** with PDF upload, automatic chunking, and vector indexing
- **Vector similarity search** across indexed document collections
- **Conversation sessions** with full message history and query refinement tracking
- **Analytics dashboard** with execution metrics, success rates, and quality scores
- **Mermaid diagram visualization** of LangGraph workflow state machines
- **User feedback system** with quality scoring (0-10) for continuous improvement
- **Rate limiting** and security middleware (Helmet, CORS)
- **Observability** with LangSmith tracing and Langfuse evaluation

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | React, TypeScript, Zustand, React Router, Mermaid.js, Axios | 19.x |
| **API Gateway** | Node.js, Express, ws, Helmet, http-proxy-middleware | 20.x |
| **Backend** | Django, Django REST Framework, Channels | 5.1 |
| **AI/ML Engine** | LangChain, LangGraph, OpenAI (GPT-4o-mini) | 0.3.x / 0.6.x |
| **Vector Store** | ChromaDB with OpenAI Embeddings (text-embedding-ada-002) | 0.6.3 |
| **Database** | PostgreSQL | 16 |
| **Cache/Broker** | Redis | 7 |
| **Observability** | LangSmith, Langfuse | — |
| **Protocols** | MCP (Model Context Protocol), A2A (Agent-to-Agent) | — |
| **Deployment** | Docker Compose (7 services, bridge network) | 3.9 |

### Backend Python Dependencies (Key)

```
django==5.1.4              djangorestframework==3.15.2
langchain==0.3.27          langgraph==0.6.6
langchain-openai==0.3.35   langchain-chroma==0.1.4
chromadb>=0.5.0,<0.7       langfuse==2.60.0
pypdf==5.4.0               tiktoken==0.9.0
celery==5.4.0              redis==5.2.1
gunicorn==23.0.0           uvicorn[standard]==0.34.0
channels==4.2.0            mcp>=1.6.0
```

### Frontend Dependencies (Key)

```
react@19.0.0               react-router-dom@7.1.1
typescript@4.9.5           zustand@5.0.3
axios@1.7.9                mermaid@11.4.1
react-markdown@9.0.3
```

### Gateway Dependencies (Key)

```
express@4.21.1             ws@8.18.0
helmet@8.0.0               http-proxy-middleware@3.0.3
express-rate-limit@7.4.1   ioredis@5.4.2
typescript@5.7.3
```

---

## Project Structure

```
AI-recursive-query-tuning-langgraph/
├── docker-compose.yml              # 7-service orchestration
├── .env                            # Environment configuration
├── .env.example                    # Template for environment variables
├── agentic_ai_research_papers.zip  # Pre-indexed research papers dataset
│
├── frontend/                       # React 19 + TypeScript
│   ├── Dockerfile                  # Multi-stage build (React → Nginx)
│   ├── package.json
│   ├── tsconfig.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.tsx                 # React Router configuration
│       ├── App.css                 # Global styles (dark theme)
│       ├── index.tsx               # Entry point
│       ├── components/
│       │   ├── Layout.tsx          # Sidebar + main layout wrapper
│       │   ├── MermaidDiagram.tsx  # LangGraph workflow renderer
│       │   └── ExecutionTrace.tsx  # Step-by-step execution viewer
│       ├── pages/
│       │   ├── ChatPage.tsx        # Main chat interface
│       │   ├── DashboardPage.tsx   # Analytics & metrics dashboard
│       │   ├── DocumentsPage.tsx   # Document upload & search
│       │   ├── WorkflowPage.tsx    # Workflow visualization
│       │   ├── AgentsPage.tsx      # Agent configuration
│       │   └── HistoryPage.tsx     # Conversation history
│       ├── services/
│       │   ├── api.ts              # REST API client (Axios)
│       │   └── websocket.ts        # WebSocket client
│       ├── store/
│       │   └── index.ts            # Zustand global state
│       └── types/
│           └── index.ts            # TypeScript type definitions
│
├── gateway/                        # Node.js Express API Gateway
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       ├── index.ts                # Server bootstrap
│       ├── routes/
│       │   ├── proxy.ts            # HTTP reverse proxy to Django
│       │   └── health.ts           # Health check endpoints
│       ├── middleware/
│       │   ├── rateLimiter.ts      # express-rate-limit middleware
│       │   └── requestLogger.ts    # Morgan request logging
│       └── websocket/
│           └── handler.ts          # WebSocket upgrade & forwarding
│
├── backend/                        # Django 5 + DRF + LangGraph
│   ├── Dockerfile
│   ├── requirements.txt            # Python dependencies
│   ├── manage.py
│   ├── core/                       # Django project configuration
│   │   ├── settings.py             # All settings (DB, cache, REST, AI)
│   │   ├── urls.py                 # Root URL routing
│   │   ├── asgi.py                 # ASGI application
│   │   └── wsgi.py                 # WSGI application
│   ├── agents/                     # Core AI/ML application
│   │   ├── models.py               # AgentConfig, WorkflowExecution, etc.
│   │   ├── views.py                # Execute, visualize, configs API
│   │   ├── serializers.py          # DRF serializers
│   │   ├── urls.py                 # Agent route definitions
│   │   ├── apps.py                 # Singleton service initialization
│   │   ├── admin.py                # Django admin registration
│   │   ├── consumers.py            # WebSocket consumer stub
│   │   ├── routing.py              # WebSocket routing
│   │   ├── services/
│   │   │   ├── langgraph_workflow.py       # RecursiveQAWorkflow (main engine)
│   │   │   ├── multi_agent_orchestrator.py # Multi-agent coordination
│   │   │   ├── document_grader.py          # Binary relevance grading
│   │   │   ├── query_rewriter.py           # Semantic query refinement
│   │   │   ├── react_agent.py              # ReAct agent implementation
│   │   │   ├── mcp_server.py               # MCP tool registry
│   │   │   ├── a2a_protocol.py             # Agent-to-Agent protocol
│   │   │   └── observability.py            # LangSmith/Langfuse integration
│   │   └── management/commands/
│   │       └── initialize_vectorstore.py   # Bootstrap ChromaDB
│   ├── documents/                  # Document management application
│   │   ├── models.py               # Document, DocumentChunk
│   │   ├── views.py                # Upload, search, list
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── admin.py
│   ├── conversations/              # Conversation history application
│   │   ├── models.py               # Session, Message, QueryRefinement
│   │   ├── views.py                # Session CRUD, message history
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── admin.py
│   └── analytics/                  # Analytics & feedback application
│       ├── models.py               # UsageMetric, QualityScore
│       ├── views.py                # Dashboard, timeline, feedback
│       ├── serializers.py
│       ├── urls.py
│       └── admin.py
│
├── nginx/
│   └── nginx.conf                  # SPA routing, gzip, security headers, caching
│
└── docs/
    ├── architecture.drawio         # Editable draw.io diagram
    └── Technical_Architecture.pptx # PowerPoint presentation
```

---

## Prerequisites

- **Docker** and **Docker Compose** (v2+)
- **OpenAI API key** with access to `gpt-4o-mini` and `text-embedding-ada-002`
- Minimum 4GB RAM available for containers
- Ports 3082-3084, 5532, 6478, 8043, 8142 available on host

---

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd AI-recursive-query-tuning-langgraph
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your **OpenAI API key** (required):

```bash
OPENAI_API_KEY=sk-your-actual-openai-api-key
```

Optionally configure LangSmith and Langfuse keys for observability:

```bash
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_TRACING_V2=true

LANGFUSE_PUBLIC_KEY=pk-lf-your-key
LANGFUSE_SECRET_KEY=sk-lf-your-key
```

> **Note:** The system auto-detects placeholder API keys and gracefully disables tracing/observability when keys are not configured. The app works fine without LangSmith or Langfuse.

### 3. Launch with Docker Compose

```bash
docker compose up --build -d
```

This builds and starts all 7 services. First boot takes 2-3 minutes as:
- PostgreSQL initializes the database
- Django runs migrations
- Backend processes and indexes the research papers into ChromaDB

### 4. Verify all services are running

```bash
docker compose ps
```

Expected output:
```
NAME            IMAGE                   STATUS          PORTS
rqt-backend     ...                     Up              0.0.0.0:8043->8043/tcp
rqt-chromadb    chromadb/chroma:0.6.3   Up (healthy)    0.0.0.0:8142->8000/tcp
rqt-frontend    ...                     Up              0.0.0.0:3082->80/tcp
rqt-gateway     ...                     Up              0.0.0.0:3083->3083/tcp
rqt-langfuse    langfuse/langfuse:2     Up              0.0.0.0:3084->3000/tcp
rqt-postgres    postgres:16-alpine      Up (healthy)    0.0.0.0:5532->5432/tcp
rqt-redis       redis:7-alpine          Up (healthy)    0.0.0.0:6478->6379/tcp
```

### 5. Access the application

| Service | URL |
|---------|-----|
| **Main Application** | `http://<HOST_IP>:3082` |
| **API Gateway** | `http://<HOST_IP>:3083` |
| **Django Admin** | `http://<HOST_IP>:8043/admin/` |
| **Langfuse Dashboard** | `http://<HOST_IP>:3084` |

Default host: `172.168.1.95` (configurable via `HOST_IP` in `.env`)

### 6. Force re-index vector store (optional)

```bash
docker compose exec backend python manage.py initialize_vectorstore --force
```

---

## Configuration

All configuration is managed via environment variables in `.env`. Key settings:

### OpenAI Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | Your OpenAI API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI API base URL |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM model for query processing |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-ada-002` | Embedding model for vector store |

### Django Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | (dev key) | Django secret key |
| `DJANGO_DEBUG` | `True` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `*` | Allowed hosts |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `http://172.168.1.95:3082` | CORS origins |

### Database & Cache

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `recursive_query_db` | Database name |
| `POSTGRES_USER` | `rqt_user` | Database user |
| `POSTGRES_PASSWORD` | `rqt_secure_password_2024` | Database password |
| `REDIS_URL` | `redis://redis:6478/0` | Redis connection URL |
| `CHROMA_HOST` | `chromadb` | ChromaDB hostname |

### Service Ports

| Variable | Default | Description |
|----------|---------|-------------|
| `FRONTEND_PORT` | `3082` | React frontend |
| `GATEWAY_PORT` | `3083` | Node.js gateway |
| `BACKEND_PORT` | `8043` | Django backend |
| `POSTGRES_EXTERNAL_PORT` | `5532` | PostgreSQL |
| `REDIS_EXTERNAL_PORT` | `6478` | Redis |
| `CHROMA_EXTERNAL_PORT` | `8142` | ChromaDB |
| `LANGFUSE_PORT` | `3084` | Langfuse |
| `MCP_SERVER_PORT` | `8045` | MCP tool server |
| `A2A_DISCOVERY_PORT` | `8044` | A2A protocol |

### Observability (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGCHAIN_TRACING_V2` | `true` | Enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | — | LangSmith API key |
| `LANGFUSE_PUBLIC_KEY` | — | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | — | Langfuse secret key |
| `LANGFUSE_HOST` | `http://langfuse:3084` | Langfuse host URL |

---

## Port Assignments

All services use non-default ports to avoid conflicts with existing services on the host machine:

| Service | External Port | Internal Port | Protocol |
|---------|:---:|:---:|----------|
| Frontend (Nginx) | **3082** | 80 | HTTP |
| API Gateway | **3083** | 3083 | HTTP + WS |
| Django Backend | **8043** | 8043 | HTTP |
| PostgreSQL | **5532** | 5432 | TCP |
| Redis | **6478** | 6379 | TCP |
| ChromaDB | **8142** | 8000 | HTTP |
| Langfuse | **3084** | 3000 | HTTP |
| MCP Server | **8045** | — | In-process |
| A2A Protocol | **8044** | — | In-process |

---

## API Reference

All API endpoints are accessed through the gateway at `http://<HOST_IP>:3083/api/`.

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/agents/execute/` | Execute a query through the AI workflow engine |
| `GET` | `/api/agents/executions/` | List all workflow executions with traces |
| `GET` | `/api/agents/executions/<id>/` | Get execution detail with full trace |
| `GET` | `/api/agents/visualize/` | Get Mermaid diagram of the workflow |
| `GET` | `/api/agents/configs/` | List agent configurations |
| `POST` | `/api/agents/configs/` | Create a new agent configuration |
| `*` | `/api/agents/mcp/*` | MCP protocol operations |
| `*` | `/api/agents/a2a/*` | A2A protocol operations |

#### Execute Query

```bash
curl -X POST http://172.168.1.95:3083/api/agents/execute/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key aspects of Agentic AI systems?",
    "workflow_type": "recursive_qa",
    "session_id": "optional-uuid"
  }'
```

Response:
```json
{
  "execution_id": "uuid",
  "status": "completed",
  "query": "What are the key aspects of Agentic AI systems?",
  "answer": "...",
  "workflow_type": "recursive_qa",
  "total_iterations": 1,
  "nodes_visited": ["generate_query_or_respond", "retrieve", "grade_documents", "generate_answer"],
  "duration_ms": 5248,
  "execution_trace": [...]
}
```

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/documents/` | List all documents |
| `POST` | `/api/documents/upload/` | Upload a document (PDF, DOCX, TXT) |
| `POST` | `/api/documents/search/` | Vector similarity search |
| `GET` | `/api/documents/<id>/` | Get document detail |

#### Upload Document

```bash
curl -X POST http://172.168.1.95:3083/api/documents/upload/ \
  -F "file=@paper.pdf" \
  -F "title=My Research Paper"
```

#### Vector Search

```bash
curl -X POST http://172.168.1.95:3083/api/documents/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "agentic AI systems", "k": 5}'
```

### Conversations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/conversations/sessions/` | List all sessions |
| `POST` | `/api/conversations/sessions/` | Create a new session |
| `GET` | `/api/conversations/sessions/<id>/` | Get session detail |
| `GET` | `/api/conversations/messages/?session=<id>` | Get messages for a session |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/analytics/dashboard/` | Dashboard overview (stats, distributions, recent executions) |
| `GET` | `/api/analytics/timeline/` | Execution timeline by period |
| `POST` | `/api/analytics/feedback/` | Submit quality feedback |

#### Submit Feedback

```bash
curl -X POST http://172.168.1.95:3083/api/analytics/feedback/ \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": "uuid-of-execution",
    "score": 8,
    "score_type": "user_satisfaction",
    "feedback": "Clear and comprehensive answer"
  }'
```

### WebSocket

```
ws://172.168.1.95:3083/ws?session_id=<session-uuid>
```

Real-time streaming of workflow execution events, including node transitions, intermediate results, and completion status.

### Health Check

```bash
curl http://172.168.1.95:3083/health
# {"status":"ok","timestamp":"...","services":{"backend":"connected"}}
```

---

## LangGraph Workflow Detail

The **RecursiveQAWorkflow** class (`backend/agents/services/langgraph_workflow.py`) implements the core Adaptive ReAct QA pattern using LangGraph's `StateGraph` with `MessagesState`.

### Workflow Graph

```
                 ┌─────────────────────────┐
                 │         START            │
                 └────────────┬────────────┘
                              │
                 ┌────────────▼────────────┐
            ┌────│ generate_query_or_respond│────────────────┐
            │    └────────────┬────────────┘                │
            │                 │ uses tools               direct answer
            │    ┌────────────▼────────────┐                │
            │    │       retrieve          │                │
            │    │     (ToolNode)          │                │
            │    └────────────┬────────────┘                │
            │                 │                             │
            │    ┌────────────▼────────────┐                │
            │    │    grade_documents       │                │
            │    │   (binary scoring)      │                │
            │    └──────┬──────────┬───────┘                │
            │           │          │                        │
            │      relevant    not relevant                 │
            │           │          │                        │
            │    ┌──────▼──────┐  ┌▼──────────────┐        │
            │    │generate_    │  │rewrite_question│        │
            │    │answer       │  └───────┬────────┘        │
            │    └──────┬──────┘          │                 │
            │           │           retry (loop back)       │
            │           │                 │                 │
            │    ┌──────▼──────┐          │                 │
            └────│     END     │◄─────────┘─────────────────┘
                 └─────────────┘
```

### LLM Configuration

| Component | Model | max_tokens | request_timeout | max_retries |
|-----------|-------|:---:|:---:|:---:|
| Main LLM | gpt-4o-mini | 500 | 30s | 1 |
| Document Grader | gpt-4o-mini | 50 | 15s | 1 |
| Query Rewriter | gpt-4o-mini | 150 | 15s | 1 |

### Vector Store Configuration

| Parameter | Value |
|-----------|-------|
| Collection | `Research_Papers` |
| Embedding Model | `text-embedding-ada-002` |
| Chunk Size | 1000 tokens |
| Chunk Overlap | 200 tokens |
| Tokenizer | `tiktoken` (cl100k_base) |
| Retriever k | 3 documents |

### Recursion Control

- **max_iterations**: 3 (default, configurable)
- **recursion_limit**: `max_iterations * 2 + 3` (LangGraph safety limit)
- Loop-back: `rewrite_question` → `generate_query_or_respond` until relevant docs found or limit reached

---

## Multi-Agent Orchestration

The **MultiAgentOrchestrator** (`backend/agents/services/multi_agent_orchestrator.py`) coordinates 5 specialized agents:

```
START → Research Agent → QA Specialist → Critique Agent ──┐
                                              ▲            │
                                              │     needs revision
                                         re-evaluate       │
                                              │            ▼
                                        Critique Agent ← Revision Agent
                                              │
                                          accepted
                                              │
                                              ▼
                                         Summarizer → END
```

Each agent has its own system prompt, temperature, and token configuration. The critique-revision loop ensures answer quality meets the configurable threshold before proceeding to summarization.

---

## Document Processing Pipeline

1. **Upload**: PDF/DOCX/TXT files uploaded via `/api/documents/upload/`
2. **Loading**: `PyPDFDirectoryLoader` extracts text from PDFs
3. **Chunking**: `RecursiveCharacterTextSplitter` with tiktoken tokenizer splits text (1000 tokens, 200 overlap)
4. **Embedding**: OpenAI `text-embedding-ada-002` generates vector embeddings
5. **Indexing**: Embeddings stored in ChromaDB under the `Research_Papers` collection
6. **Retrieval**: Similarity search returns top-k chunks for RAG workflow

On first boot, the system automatically processes `agentic_ai_research_papers.zip` and indexes all papers.

---

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| **Chat** | `/chat` | Main interface for querying the AI system. Select workflow type (Recursive ReAct QA or Multi-Agent), enter questions, and see streaming responses. |
| **Dashboard** | `/dashboard` | Analytics overview: total queries, success rate, average duration, active sessions, document count, quality scores, workflow distribution, recent executions. |
| **Documents** | `/documents` | Upload new documents, view indexed documents, and perform vector similarity searches. |
| **Workflow** | `/workflow` | Interactive Mermaid.js visualization of LangGraph workflow state machines for both QA and multi-agent workflows. |
| **Agents** | `/agents` | View and configure agent settings: model selection, temperature, max tokens, system prompts. |
| **History** | `/history` | Browse conversation sessions and review full message history with execution traces. |

---

## Database Schema

### Core Models

```
┌─────────────────────────┐   ┌──────────────────────────┐
│     AgentConfig          │   │   WorkflowExecution       │
├─────────────────────────┤   ├──────────────────────────┤
│ id (UUID, PK)           │   │ id (UUID, PK)            │
│ name                    │   │ workflow_type             │
│ agent_type (choice)     │   │ status (choice)          │
│ model_name              │   │ input_query              │
│ temperature             │   │ final_answer             │
│ max_tokens              │   │ total_iterations         │
│ system_prompt           │   │ nodes_visited (JSON)     │
│ is_active               │   │ execution_trace (JSON)   │
│ created_at / updated_at │   │ mermaid_diagram          │
└─────────────────────────┘   │ duration_ms              │
                              │ started_at / completed_at│
                              └──────────────────────────┘

┌─────────────────────────┐   ┌──────────────────────────┐
│      Document            │   │    DocumentChunk          │
├─────────────────────────┤   ├──────────────────────────┤
│ id (UUID, PK)           │   │ id (UUID, PK)            │
│ title, description      │   │ document_id (FK)         │
│ file_path, file_upload  │   │ chunk_index              │
│ document_type           │   │ content                  │
│ file_size, page_count   │   │ page_number              │
│ chunk_count             │   │ token_count              │
│ status (choice)         │   │ embedding_id             │
│ collection_name         │   │ metadata (JSON)          │
│ uploaded_at / indexed_at│   └──────────────────────────┘
└─────────────────────────┘

┌─────────────────────────┐   ┌──────────────────────────┐
│       Session            │   │       Message             │
├─────────────────────────┤   ├──────────────────────────┤
│ id (UUID, PK)           │   │ id (UUID, PK)            │
│ title, description      │   │ session_id (FK)          │
│ is_active               │   │ role (choice)            │
│ metadata (JSON)         │   │ content                  │
│ created_at / updated_at │   │ tool_calls (JSON)        │
└─────────────────────────┘   │ workflow_execution_id    │
                              │ metadata (JSON)          │
                              │ created_at               │
                              └──────────────────────────┘

┌─────────────────────────┐   ┌──────────────────────────┐
│    QueryRefinement       │   │     QualityScore          │
├─────────────────────────┤   ├──────────────────────────┤
│ id (UUID, PK)           │   │ id (UUID, PK)            │
│ session_id (FK)         │   │ workflow_execution_id    │
│ original_query          │   │ score_type (choice)      │
│ refined_query           │   │ score (float, 0-10)      │
│ iteration               │   │ feedback (text)          │
│ reason                  │   │ created_at               │
│ created_at              │   └──────────────────────────┘
└─────────────────────────┘
```

---

## Observability & Monitoring

### LangSmith Integration
- Full LangChain run tracing when `LANGCHAIN_TRACING_V2=true` and a valid API key
- Tracks each LLM call, tool invocation, and chain execution
- Automatically disabled when placeholder keys are detected

### Langfuse Integration
- Self-hosted observability platform on port 3084
- Trace scoring and evaluation for workflow executions
- Default admin: `admin@rqt.local` / `admin123`
- Callback handlers cached as singletons for performance

### Placeholder Key Detection
The system automatically detects placeholder API keys matching patterns like `your-`, `change-me`, `placeholder`, `xxx`, etc. When detected:
- LangSmith tracing is force-disabled (`LANGCHAIN_TRACING_V2=false`)
- Langfuse callbacks are skipped
- The app continues to function normally without observability

### Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f gateway

# Backend query execution logs
docker compose logs -f backend | grep WORKFLOW
```

---

## Protocol Integrations

### MCP (Model Context Protocol) — Port 8045
- In-memory tool registry for standardized tool invocation
- Registers the `retrieve_scientific_papers` tool
- Accessible via `/api/agents/mcp/` endpoints
- Follows the MCP specification for tool discovery and execution

### A2A (Agent-to-Agent) — Port 8044
- Inter-agent discovery and task delegation protocol
- Enables agents to discover each other's capabilities
- Supports asynchronous task delegation and message passing
- Protocol version 0.1

---

## Key Architecture Decisions

### Gateway Body Re-serialization
Express's `express.json()` middleware consumes the request body stream before `http-proxy-middleware` can pipe it to the backend. The gateway re-serializes `req.body` in the `proxyReq` handler to prevent POST requests from hanging.

### Gateway TypeScript Recompilation
The gateway Dockerfile compiles TypeScript at build time. For development, docker-compose overrides the command with `sh -c "npx tsc && node dist/index.js"` so volume-mounted source changes take effect on container restart.

### Singleton Service Management
The workflow engine, vectorstore, multi-agent orchestrator, MCP server, and A2A handler are initialized once in Django's `AppConfig.ready()` and accessed via module-level getter functions. This avoids expensive re-initialization per request.

### Non-Default Ports
All services use non-standard ports (5532, 6478, 8142, etc.) to avoid conflicts with other services running on the host machine.

### Recursive Loop Safety
LangGraph's recursion limit is set to `max_iterations * 2 + 3` to allow for the expected number of state transitions while preventing infinite loops from consuming resources.

### Synchronous Workflow Execution
The `RecursiveQAWorkflow.execute()` method is synchronous (LangGraph's `graph.invoke()` is sync). This eliminates unnecessary async/sync wrapping overhead that previously caused issues with event loop management.

---

## Development Guide

### Rebuild a single service

```bash
docker compose up -d --build <service>   # e.g., frontend, gateway, backend
```

### Access Django shell

```bash
docker compose exec backend python manage.py shell
```

### Run Django management commands

```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

### View real-time logs

```bash
docker compose logs -f backend gateway
```

### Reset everything

```bash
docker compose down -v    # removes volumes (data loss!)
docker compose up --build -d
```

---

## Troubleshooting

### Query hangs / never completes
1. **Check OpenAI API key**: Ensure `OPENAI_API_KEY` in `.env` is a real, valid key
2. **Check LangSmith key**: If `LANGCHAIN_TRACING_V2=true`, ensure the API key is valid — placeholder keys cause hangs. Set `LANGCHAIN_TRACING_V2=false` to disable.
3. **Check gateway logs**: `docker compose logs -f gateway` — POST requests should appear
4. **Rebuild gateway**: After editing gateway TypeScript, restart: `docker compose restart gateway`

### "Not Found" errors in backend logs
- Ensure the gateway proxy's `pathRewrite` adds `/api/` prefix back
- Check `BACKEND_URL` environment variable in gateway (should be `http://backend:8043`)

### ChromaDB not healthy
- First boot takes 20-30 seconds for ChromaDB to start
- Check: `docker compose logs chromadb`
- Verify port 8142 is available on host

### Frontend not loading
- Rebuild: `docker compose up -d --build frontend`
- Check Nginx config: `nginx/nginx.conf`
- Verify `REACT_APP_GATEWAY_URL` points to correct gateway address

### Dashboard shows "Avg Quality N/A"
- Quality scores require user feedback submissions
- Use the feedback API or chat interface to submit quality ratings

---

## Documentation Artifacts

| File | Description |
|------|-------------|
| [`docs/architecture.drawio`](docs/architecture.drawio) | Editable technical architecture diagram — open in [draw.io](https://app.diagrams.net) |
| [`docs/Technical_Architecture.pptx`](docs/Technical_Architecture.pptx) | 6-slide PowerPoint presentation: Title, System Architecture, LangGraph Workflow, Multi-Agent Orchestration, API & Data Flow, Deployment & Ports |

---

## License

This project is for educational and research purposes.
