"""FastAPI web server for the OmniParser-RAG chat frontend."""

from contextlib import asynccontextmanager
import logging
from pathlib import Path

import anyio
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents.graph_retriever import GraphRetriever
from agents.llm_client import LLMClient
from config import settings
from database.code_graph import CodeGraph
from database.vector_client import VectorClient

logger = logging.getLogger("omniparser.server")

_STATIC_DIR = Path(__file__).parent / "static"


class QueryRequest(BaseModel):
    """Request body for the /api/query endpoint."""

    question: str
    top_k: int = settings.VECTOR_SEARCH_TOP_K


class QueryResponse(BaseModel):
    """Response body returned by the /api/query endpoint."""

    answer: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: open DB connections on startup, close on shutdown."""
    logger.info("Starting up: initialising database connections...")
    graph_db = CodeGraph(settings.NEO4J_URI, settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
    vector_db = VectorClient()
    retriever = GraphRetriever(vector_client=vector_db, neo4j_client=graph_db)
    app.state.llm_client = LLMClient(retriever=retriever)
    app.state.graph_db = graph_db
    logger.info("Startup complete.")
    yield
    logger.info("Shutting down: closing Neo4j connection...")
    app.state.graph_db.close()


app = FastAPI(title="OmniParser-RAG", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serve the chat frontend."""
    index_path = _STATIC_DIR / "index.html"
    logger.debug("Serving index from: %s (exists=%s)", index_path, index_path.exists())
    return FileResponse(index_path)


@app.post("/api/query", response_model=QueryResponse)
async def api_query(req: QueryRequest):
    """Run a RAG query and return the LLM-generated answer."""
    if not req.question.strip():
        raise HTTPException(status_code=422, detail="Question must not be empty.")
    llm_client = app.state.llm_client
    # LLMClient.ask() is a blocking call — run in a thread to avoid blocking the event loop
    answer = await anyio.to_thread.run_sync(lambda: llm_client.ask(req.question, top_k=req.top_k))
    return QueryResponse(answer=answer)
