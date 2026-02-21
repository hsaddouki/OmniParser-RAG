import logging

from config import settings
from utils import trace

logger = logging.getLogger("omniparser.graph_retriever")


class GraphRetriever:
    """GraphRetriever class for retrieving context from graph database."""

    def __init__(self, vector_client, neo4j_client):
        self.vector_db = vector_client
        self.graph_db = neo4j_client

    @trace
    def retrieve_context(self, query: str, k: int = settings.VECTOR_SEARCH_TOP_K) -> str:
        """
        Retrieves context from both databases using semantic similarity.

        Uses cosine similarity to find the most similar code units.
        """
        context_blocks = []

        # 1. Semantic search using ChromaDB
        logger.info("Running semantic search for: %s", query)
        semantic_results = self.vector_db.search(query, k=k)
        logger.debug("Vector search returned %d result(s):", len(semantic_results))
        for i, r in enumerate(semantic_results):
            logger.debug(
                "  [%d] name=%r  file=%r  content=%r",
                i,
                r.metadata.get("name"),
                r.metadata.get("file"),
                r.page_content[:120],
            )

        # 2. Structural search using Neo4j
        for result in semantic_results:
            func_name = result.metadata["name"]
            file_name = result.metadata["file"]

            # Query Neo4j for structural relationships around this function
            structural_context = self.graph_db.get_related_entities(func_name, file_name=file_name)
            logger.debug("  Graph context for %r: %s", func_name, structural_context)

            text_block = f"""
            Code Unit: {func_name}
            File: {file_name}
            Content: {result.page_content}
            Graph Relationships: {structural_context}
            """

            context_blocks.append(text_block)

        full_context = "\n".join(context_blocks)
        logger.debug("Assembled context (%d chars):\n%s", len(full_context), full_context[:800])
        return full_context
