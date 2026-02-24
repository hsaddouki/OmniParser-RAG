"""OmniParser-RAG — CLI entry point.

Usage:
    python src/main.py --help
    python src/main.py ingest --repo-path /path/to/repo
    python src/main.py query "How does the authentication module work?"
    python src/main.py status
"""

import argparse
import logging
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

from config import settings

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

REQUIRED_ENV_VARS = [
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "OLLAMA_EMBEDDING_MODEL",
    "NEO4J_URI",
    "NEO4J_USERNAME",
    "NEO4J_PASSWORD",
    "NEO4J_DATABASE",
    "CHROMA_PERSIST_PATH",
    "CHROMA_COLLECTION_NAME",
]


def load_environment() -> None:
    """Load .env file into the process environment."""
    load_dotenv()


def validate_environment() -> None:
    """Check all required env vars are set; exit with a clear error if not."""
    logger = logging.getLogger("omniparser.env")
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        logger.error(
            "Missing required environment variables:\n%s\n"
            "Copy .env.example to .env and fill in the missing values.",
            "\n".join(f"  - {v}" for v in missing),
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def configure_logging() -> None:
    """Set up structured logging based on LOG_LEVEL env var."""
    level_name = settings.LOG_LEVEL.upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------


def cmd_ingest(args: argparse.Namespace) -> None:
    """Ingest a source code repository into ChromaDB + Neo4j."""
    from pathlib import Path

    from parser.ingestor import run_ingestor

    logger = logging.getLogger("omniparser.ingest")

    # Validate repo path exists
    repo_path = Path(args.repo_path).resolve()
    if not repo_path.is_dir():
        logger.error("Repository path does not exist or is not a directory: %s", repo_path)
        sys.exit(1)

    # Warn if unsupported language requested
    if args.language != "python":
        logger.warning(
            "Language %r is not yet supported — only Python is available. Proceeding with Python parser.",
            args.language,
        )

    logger.info("Ingestion started for repo: %s", repo_path)

    try:
        data = run_ingestor(str(repo_path))
    except Exception as exc:
        logger.error(
            "Ingestion failed. Ensure Ollama, Neo4j, and ChromaDB are running. Error: %s", exc
        )
        sys.exit(1)

    logger.info(
        "Ingestion complete — %d file(s) analysed, %d function(s) indexed, %d import relationship(s) created.",
        data["total_files"],
        data["total_functions"],
        len(data.get("imports", [])),
    )


def cmd_query(args: argparse.Namespace) -> None:
    """Run a RAG query against the indexed codebase."""
    logger = logging.getLogger("omniparser.query")
    from agents.graph_retriever import GraphRetriever
    from agents.llm_client import LLMClient
    from database.code_graph import CodeGraph
    from database.vector_client import VectorClient

    graph_db = CodeGraph(settings.NEO4J_URI, settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
    vector_db = VectorClient()
    retriever = GraphRetriever(vector_client=vector_db, neo4j_client=graph_db)
    client = LLMClient(retriever=retriever)

    logger.info("Query: %r", args.question)
    answer = client.ask(args.question, top_k=args.top_k)
    print(answer)
    graph_db.close()


def cmd_serve(args: argparse.Namespace) -> None:
    """Start the FastAPI chat server."""
    import uvicorn

    logger = logging.getLogger("omniparser.serve")
    logger.info("Starting server on http://%s:%d", args.host, args.port)
    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        app_dir=str(Path(__file__).parent),
        log_level=settings.LOG_LEVEL.lower(),
    )


def cmd_status(args: argparse.Namespace) -> None:
    """Check live connectivity to Ollama, Neo4j, and ChromaDB."""
    import urllib.error
    import urllib.request

    logger = logging.getLogger("omniparser.status")

    # --- Ollama ---
    try:
        with urllib.request.urlopen(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5) as resp:  # noqa: S310
            if resp.status == 200:
                logger.info("Ollama      [OK]  %s", settings.OLLAMA_BASE_URL)
            else:
                logger.warning("Ollama      [WARN] status=%d", resp.status)
    except Exception as exc:
        logger.error("Ollama      [FAILED] %s — %s", settings.OLLAMA_BASE_URL, exc)

    # --- Neo4j ---
    try:
        from neo4j import GraphDatabase  # type: ignore[import]

        driver = GraphDatabase.driver(
            settings.NEO4J_URI, auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
        driver.close()
        logger.info("Neo4j       [OK]  %s", settings.NEO4J_URI)
    except Exception as exc:
        logger.error("Neo4j       [FAILED] %s", exc)

    # --- ChromaDB ---
    try:
        import chromadb  # type: ignore[import]

        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_PATH)
        client.heartbeat()
        logger.info("ChromaDB    [OK]  persist_path=%s", settings.CHROMA_PERSIST_PATH)
    except Exception as exc:
        logger.error("ChromaDB    [FAILED] %s", exc)


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="omniparser-rag",
        description="OmniParser-RAG: local LLM + hybrid GraphRAG for code analysis.",
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # ingest
    p_ingest = sub.add_parser("ingest", help="Index a source code repository.")
    p_ingest.add_argument(
        "--repo-path",
        required=True,
        metavar="PATH",
        help="Path to the root of the repository to ingest.",
    )
    p_ingest.add_argument(
        "--language",
        default="python",
        metavar="LANG",
        help="Primary programming language (default: python).",
    )
    p_ingest.set_defaults(func=cmd_ingest)

    # query
    p_query = sub.add_parser("query", help="Ask a question about the indexed codebase.")
    p_query.add_argument("question", help="Natural-language question or code generation prompt.")
    p_query.add_argument(
        "--top-k",
        type=int,
        default=settings.VECTOR_SEARCH_TOP_K,
        metavar="N",
        help="Number of vector-search results to retrieve (default: VECTOR_SEARCH_TOP_K env var).",
    )
    p_query.set_defaults(func=cmd_query)

    # status
    p_status = sub.add_parser("status", help="Check connectivity to Ollama, Neo4j, and ChromaDB.")
    p_status.set_defaults(func=cmd_status)

    # serve
    p_serve = sub.add_parser("serve", help="Start the web chat server.")
    p_serve.add_argument(
        "--host",
        default="0.0.0.0",  # noqa: S104
        help="Bind host (default: 0.0.0.0 — all interfaces).",
    )
    p_serve.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Bind port (default: 8000).",
    )
    p_serve.add_argument(
        "--reload",
        action="store_true",
        default=False,
        help="Enable uvicorn auto-reload (development only).",
    )
    p_serve.set_defaults(func=cmd_serve)

    return parser


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI arguments, validate environment, and dispatch subcommand."""
    load_environment()
    configure_logging()

    parser = build_parser()
    args = parser.parse_args()

    # Status does not require all env vars to be set (useful for debugging)
    if args.command != "status":
        validate_environment()

    args.func(args)


if __name__ == "__main__":
    main()
