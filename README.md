# OmniParser-RAG

**Local LLM + hybrid GraphRAG for code analysis and question answering.**

OmniParser-RAG lets you index a Python codebase and ask natural-language questions about it—entirely on your own machine. It combines semantic vector search (ChromaDB) with structural graph traversal (Neo4j) to retrieve rich, relationship-aware context, then passes that context to a local LLM served by Ollama.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

---

## Architecture

```
Source Code
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Ingestion (WIP)                                    │
│  AST Parser → extract symbols, relationships        │
│      │                       │                      │
│      ▼                       ▼                      │
│  ChromaDB             Neo4j Graph Store             │
│  (vector embeddings)  (function/class graph)        │
└─────────────────────────────────────────────────────┘
    │                          │
    └──────────┬───────────────┘
               ▼
     Hybrid GraphRetriever
     (vector search + graph traversal → merged context)
               │
               ▼
     Ollama LLM (local)
               │
               ▼
          Answer / Analysis
```

**Retrieval strategy:** on each query, the `GraphRetriever` runs a vector similarity search against ChromaDB and a depth-bounded graph traversal in Neo4j in parallel, then merges the results before sending them to the LLM.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| **Python 3.10+** | |
| **Ollama** | Running locally at `http://localhost:11434`. [Install](https://ollama.com) |
| **Docker + Docker Compose** | For Neo4j and ChromaDB containers |

### Pull required Ollama models

```bash
ollama pull llama3.1            # chat/generation model
ollama pull nomic-embed-text    # embedding model
```

---

## Installation

```bash
git clone https://github.com/your-org/OmniParser-RAG.git
cd OmniParser-RAG

# Install Python dependencies
pip install -r requirements.txt

# Create your local environment config
cp .env.example .env
```

Edit `.env` and set at minimum your Neo4j password to match what Docker uses (see [Configuration](#configuration)).

---

## Starting Services

Start Neo4j and ChromaDB with Docker Compose:

```bash
docker-compose up -d
```

Services started:

| Service  | Port | URL / Protocol |
|----------|------|----------------|
| Neo4j Web UI | 7474 | http://localhost:7474 |
| Neo4j Bolt | 7687 | bolt://localhost:7687 |
| ChromaDB | 8000 | http://localhost:8000 |

The default Neo4j credentials set in `docker-compose.yml` are `neo4j / password123`. Update `NEO4J_PASSWORD` in your `.env` file to match.

---

## Usage

All commands are run from the project root with `python src/main.py`.

### Check connectivity

Verify that Ollama, Neo4j, and ChromaDB are all reachable:

```bash
python src/main.py status
```

Example output:

```
2024-01-15T10:23:01 [INFO] omniparser.status — Ollama      [OK]  http://localhost:11434
2024-01-15T10:23:01 [INFO] omniparser.status — Neo4j       [OK]  bolt://localhost:7687
2024-01-15T10:23:01 [INFO] omniparser.status — ChromaDB    [OK]  persist_path=./chroma_data
```

### Ingest a repository *(work in progress)*

> **Note:** The `ingest` command exists in the CLI but is a placeholder. The AST-based parser logic is implemented in `src/parser/ingestor.py`, but the ingestion pipeline is not yet wired to the CLI. This is the next development milestone.

```bash
python src/main.py ingest --repo-path /path/to/your/repo
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--repo-path PATH` | *(required)* | Path to the repository root |
| `--language LANG` | `python` | Primary language (only Python is supported) |

### Query the codebase

Ask a natural-language question about an already-indexed codebase:

```bash
python src/main.py query "How does the authentication module work?"
```

```bash
python src/main.py query "What functions call the database connection?" --top-k 10
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `question` | *(required)* | Natural-language question or code generation prompt |
| `--top-k N` | `5` (env: `VECTOR_SEARCH_TOP_K`) | Number of vector-search results to retrieve |

---

## Configuration

Copy `.env.example` to `.env` and set the values below. All settings have sensible defaults for local development.

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1` | Chat/generation model name |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model name |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt connection URI |
| `NEO4J_USERNAME` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | *(set me)* | Neo4j password — must match `docker-compose.yml` |
| `NEO4J_DATABASE` | `neo4j` | Neo4j database name |
| `CHROMA_PERSIST_PATH` | `./chroma_data` | Local path for ChromaDB persistence |
| `CHROMA_COLLECTION_NAME` | `codebase_embeddings` | ChromaDB collection name |
| `CHROMA_HOST` | `localhost` | ChromaDB host (for HTTP client mode) |
| `CHROMA_PORT` | `8000` | ChromaDB port |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `VECTOR_SEARCH_TOP_K` | `5` | Default number of vector search results |
| `GRAPH_TRAVERSAL_MAX_DEPTH` | `3` | Max depth for Neo4j graph traversal |

---

## Project Structure

```
OmniParser-RAG/
├── src/
│   ├── main.py                  # CLI entry point (ingest / query / status)
│   ├── config/
│   │   └── settings.py          # Env var loading and defaults
│   ├── agents/
│   │   ├── graph_retriever.py   # Hybrid retriever (vector + graph)
│   │   └── llm_client.py        # Ollama LLM wrapper
│   ├── database/
│   │   ├── code_graph.py        # Neo4j client
│   │   └── vector_client.py     # ChromaDB client
│   ├── parser/
│   │   └── ingestor.py          # AST-based Python code parser
│   └── utils/
├── tests/
│   └── test_env.py
├── docker-compose.yml           # Neo4j + ChromaDB services
├── .env.example                 # Config template
└── requirements.txt
```

---

## Current Status

| Feature | Status | Notes |
|---------|--------|-------|
| ChromaDB vector client | ✅ Implemented | Persistent local storage |
| Neo4j graph client | ✅ Implemented | Bolt protocol |
| Ollama LLM client | ✅ Implemented | Chat + embeddings |
| Hybrid GraphRetriever | ✅ Implemented | Parallel vector + graph retrieval |
| `query` CLI command | ✅ Implemented | Full end-to-end |
| `status` CLI command | ✅ Implemented | Connectivity checks |
| AST-based Python parser | ✅ Implemented | `src/parser/ingestor.py` |
| `ingest` CLI command | ⚠️ Placeholder | Parser exists; pipeline not wired to CLI yet |
| Self-correcting loop | ❌ Planned | Retry logic on generation errors |
| Class hierarchy extraction | ❌ Planned | Extract and graph class inheritance |
| Multi-language support | ❌ Planned | Currently Python only |

---

## License

MIT
