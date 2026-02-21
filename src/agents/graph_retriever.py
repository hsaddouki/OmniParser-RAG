import logging

from utils import trace

logger = logging.getLogger("omniparser.graph_retriever")


class GraphRetriever:
    """GraphRetriever class for retrieving context from graph database."""

    def __init__(self, vector_client, neo4j_client):
        self.vector_db = vector_client
        self.graph_db = neo4j_client

    @trace
    def retrieve_context(self, query: str) -> str:
        """
        Obtenemos el contexto de la base de datos de grafos buscando semánticamente.

        Usa la similitud del coseno para encontrar las unidades de código más similares.
        """
        context_blocks = []

        # 1. Buscamos semanticamente usando ChromaDB
        logger.info("Buscando semánticamente: %s", query)
        semantic_results = self.vector_db.search(query, k=2)

        # 2. Buscamos de forma estructural usando Neo4j
        for result in semantic_results:
            func_name = result.metadata["name"]
            file_name = result.metadata["file"]

            # Pedimos a Neo4j que entidades llama a esta función para entender el impacto
            structural_context = self.graph_db.get_related_entities(func_name)

            text_block = f"""
            Unidad de Código: {func_name}
            Archivo: {file_name}
            Contenido: {result.page_content}
            Relaciones en el Grafo: {structural_context}
            """

            context_blocks.append(text_block)

        return "\n".join(context_blocks)
