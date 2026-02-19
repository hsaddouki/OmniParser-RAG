"""
OmniParser-RAG — CLI entry point.

Usage:
    python src/main.py --help
    python src/main.py ingest --repo-path /path/to/repo
    python src/main.py query "How does the authentication module work?"
    python src/main.py status
"""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

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
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        print(
            f"[ERROR] Missing required environment variables:\n"
            + "\n".join(f"  - {v}" for v in missing)
            + "\n\nCopy .env.example to .env and fill in the missing values.",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def configure_logging() -> None:
    """Set up structured logging based on LOG_LEVEL env var."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
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
    """Placeholder: ingest a source code repository into ChromaDB + Neo4j."""
    logger = logging.getLogger("omniparser.ingest")
    logger.info("Ingestion started for repo: %s (language: %s)", args.repo_path, args.language)
    # TODO: implement ingestion pipeline (parser → embedder → vector store + graph store)
    logger.info("Ingestion complete (placeholder — not yet implemented).")


def cmd_query(args: argparse.Namespace) -> None:
    """Placeholder: run a RAG query against the indexed codebase."""
    logger = logging.getLogger("omniparser.query")
    logger.info("Query: %r  (top_k=%d)", args.question, args.top_k)
    # TODO: implement hybrid retrieval (ChromaDB + Neo4j) → LLM generation
    logger.info("Query complete (placeholder — not yet implemented).")


def cmd_status(args: argparse.Namespace) -> None:  # noqa: ARG001
    """Check live connectivity to Ollama, Neo4j, and ChromaDB."""
    import urllib.request
    import urllib.error

    logger = logging.getLogger("omniparser.status")

    # --- Ollama ---
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        with urllib.request.urlopen(f"{ollama_url}/api/tags", timeout=5) as resp:
            if resp.status == 200:
                logger.info("Ollama      [OK]  %s", ollama_url)
            else:
                logger.warning("Ollama      [WARN] status=%d", resp.status)
    except Exception as exc:
        logger.error("Ollama      [FAILED] %s — %s", ollama_url, exc)

    # --- Neo4j ---
    try:
        from neo4j import GraphDatabase  # type: ignore[import]

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        driver.close()
        logger.info("Neo4j       [OK]  %s", uri)
    except Exception as exc:
        logger.error("Neo4j       [FAILED] %s", exc)

    # --- ChromaDB ---
    try:
        import chromadb  # type: ignore[import]

        persist_path = os.getenv("CHROMA_PERSIST_PATH", "./chroma_data")
        client = chromadb.PersistentClient(path=persist_path)
        client.heartbeat()
        logger.info("ChromaDB    [OK]  persist_path=%s", persist_path)
    except Exception as exc:
        logger.error("ChromaDB    [FAILED] %s", exc)


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
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
        default=int(os.getenv("VECTOR_SEARCH_TOP_K", "5")),
        metavar="N",
        help="Number of vector-search results to retrieve (default: VECTOR_SEARCH_TOP_K env var).",
    )
    p_query.set_defaults(func=cmd_query)

    # status
    p_status = sub.add_parser("status", help="Check connectivity to Ollama, Neo4j, and ChromaDB.")
    p_status.set_defaults(func=cmd_status)

    return parser


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
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
