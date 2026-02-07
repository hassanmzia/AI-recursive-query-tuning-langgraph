# AI Recursive Query Tuning — LangGraph Multi-Agent System

A professional-grade AI-powered recursive query and answer tuning application built with LangGraph, featuring multi-agent orchestration, adaptive ReAct patterns, and comprehensive observability.

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    http://172.168.1.95:3082                     │
│                  React/TypeScript Frontend                      │
│            (Nginx · Port 3082 — Main Site)                     │
└──────────────────────┬─────────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────────┐
│              Node.js API Gateway (Port 3083)                    │
│         Express · WebSocket · Rate Limiting · CORS              │
└──────────────────────┬─────────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────────┐
│              Django Backend (Port 8042)                          │
│    LangChain · LangGraph · Multi-Agent · MCP · A2A              │
├─────────────┬──────────────┬──────────────┬────────────────────┤
│  PostgreSQL │   ChromaDB   │    Redis     │     Langfuse       │
│  Port 5532  │  Port 8142   │  Port 6479   │    Port 3084       │
└─────────────┴──────────────┴──────────────┴────────────────────┘
```

## Features

### Core AI Workflows (from notebook)
- **Adaptive ReAct QA Workflow** — Recursive question reframing with document grading
  - `generate_query_or_respond` — Decides to answer directly or use RAG retrieval
  - `retrieve` (ToolNode) — Fetches relevant chunks from ChromaDB vector store
  - `grade_documents` — Binary relevance evaluation of retrieved documents
  - `rewrite_question` — Refines unclear queries for better retrieval
  - `generate_answer` — Produces final answer from context (max 3 sentences)

### Multi-Agent System
- **Research Agent** — Searches and analyzes research papers
- **QA Specialist** — Synthesizes research findings into clear answers
- **Critique Agent** — Evaluates answer quality (1-10 score) with feedback
- **Revision Agent** — Improves answers based on critique
- **Summarization Agent** — Creates concise final summaries

### Protocol Integrations
- **MCP (Model Context Protocol)** — Standardized tool registry and invocation
- **A2A (Agent-to-Agent)** — Inter-agent discovery, task delegation, and messaging
- **LangSmith** — Tracing and debugging for LangChain workflows
- **Langfuse** — Observability, scoring, and evaluation platform

### Application Features
- Real-time WebSocket streaming of workflow execution
- Document upload with automatic PDF processing and vector indexing
- Vector store similarity search
- Conversation session management with history
- Analytics dashboard with execution metrics
- Mermaid diagram workflow visualization
- LangGraph state graph visualization
- User feedback and quality scoring
- Rate limiting and caching

## Port Assignments (all non-default)

| Service      | Port  | Description                    |
|-------------|-------|--------------------------------|
| Frontend    | 3082  | Main site (React via Nginx)    |
| Gateway     | 3083  | Node.js API Gateway + WS       |
| Backend     | 8042  | Django REST API + ASGI          |
| PostgreSQL  | 5532  | Database                        |
| Redis       | 6479  | Cache / Message Broker          |
| ChromaDB    | 8142  | Vector Store                    |
| Langfuse    | 3084  | Observability Platform          |

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### 2. Launch with Docker Compose

```bash
docker compose up --build -d
```

### 3. Access the application

- **Main Site**: http://172.168.1.95:3082
- **API Gateway**: http://172.168.1.95:3083
- **Django Admin**: http://172.168.1.95:8042/admin/
- **Langfuse**: http://172.168.1.95:3084

### 4. Initialize vector store (automatic on first boot)

The backend automatically processes `agentic_ai_research_papers.zip` on startup. To force re-indexing:

```bash
docker compose exec backend python manage.py initialize_vectorstore --force
```

## Technology Stack

| Layer         | Technology                                            |
|--------------|------------------------------------------------------|
| Frontend     | React 19, TypeScript, Zustand, Mermaid.js             |
| API Gateway  | Node.js, Express, WebSocket (ws), http-proxy-middleware|
| Backend      | Django 5, DRF, Channels, Gunicorn + Uvicorn           |
| AI/ML        | LangChain, LangGraph, OpenAI GPT-4o-mini              |
| Vector Store | ChromaDB with OpenAI Embeddings                       |
| Database     | PostgreSQL 16                                          |
| Cache        | Redis 7                                                |
| Observability| LangSmith, Langfuse                                   |
| Protocols    | MCP (Model Context Protocol), A2A (Agent-to-Agent)    |
| Deployment   | Docker Compose                                         |

## API Endpoints

### Agents
- `POST /api/agents/execute/` — Execute a query through AI workflow
- `GET  /api/agents/executions/` — List workflow executions
- `GET  /api/agents/visualize/` — Get workflow Mermaid diagram
- `GET  /api/agents/configs/` — Agent configurations
- `*    /api/agents/mcp/` — MCP tool operations
- `*    /api/agents/a2a/` — A2A protocol operations

### Documents
- `POST /api/documents/upload/` — Upload and index a document
- `POST /api/documents/search/` — Search vector store
- `GET  /api/documents/` — List documents

### Conversations
- `GET  /api/conversations/sessions/` — List sessions
- `POST /api/conversations/sessions/` — Create session

### Analytics
- `GET  /api/analytics/dashboard/` — Dashboard metrics
- `POST /api/analytics/feedback/` — Submit quality feedback

### WebSocket
- `ws://172.168.1.95:3083/ws?session_id=<id>` — Real-time workflow streaming
