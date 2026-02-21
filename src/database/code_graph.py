import logging

from neo4j import GraphDatabase

from utils import trace

logger = logging.getLogger("omniparser.code_graph")


class CodeGraph:
    """Manages code relationship data in a Neo4j graph database."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    @trace
    def close(self) -> None:
        """Close the Neo4j driver connection."""
        self.driver.close()

    @trace
    def add_function(self, file_name: str, func_name: str, docstring: str) -> None:
        """Create or merge a file→function relationship in the graph."""
        with self.driver.session() as session:
            # Esta consulta Cypher crea el archivo, la función y los conecta
            query = """
            MERGE (f:File {name: $file_name})
            MERGE (fn:Function {name: $func_name, file: $file_name})
            SET fn.docstring = $docstring
            MERGE (f)-[:CONTAINS]->(fn)
            """
            session.run(query, file_name=file_name, func_name=func_name, docstring=docstring)

    @trace
    def add_import(self, source_file: str, target_file: str) -> None:
        """Create an IMPORTS relationship between two File nodes."""
        with self.driver.session() as session:
            query = """
            MERGE (src:File {name: $source})
            MERGE (tgt:File {name: $target})
            MERGE (src)-[:IMPORTS]->(tgt)
            """
            session.run(query, source=source_file, target=target_file)

    @trace
    def get_related_entities(self, func_name: str, file_name: str | None = None) -> str:
        """Return a human-readable string of graph relationships for a function."""
        logger.debug("Graph lookup for func_name=%r file_name=%r", func_name, file_name)
        with self.driver.session() as session:
            if file_name:
                query = """
                MATCH (fn:Function {name: $func_name, file: $file_name})<-[:CONTAINS]-(f:File)
                OPTIONAL MATCH (f)-[:CONTAINS]->(sibling:Function)
                WHERE sibling.name <> $func_name
                OPTIONAL MATCH (importing:File)-[:IMPORTS]->(f)
                RETURN f.name AS file,
                       collect(DISTINCT sibling.name) AS siblings,
                       collect(DISTINCT importing.name) AS imported_by
                """
                result = session.run(query, func_name=func_name, file_name=file_name).single()
            else:
                query = """
                MATCH (fn:Function {name: $func_name})<-[:CONTAINS]-(f:File)
                OPTIONAL MATCH (f)-[:CONTAINS]->(sibling:Function)
                WHERE sibling.name <> $func_name
                OPTIONAL MATCH (importing:File)-[:IMPORTS]->(f)
                RETURN f.name AS file,
                       collect(DISTINCT sibling.name) AS siblings,
                       collect(DISTINCT importing.name) AS imported_by
                """
                result = session.run(query, func_name=func_name).single()
            if not result:
                logger.debug("  → No node found for %r", func_name)
                return "No graph relationships found."
            logger.debug(
                "  → file=%r  siblings=%r  imported_by=%r",
                result["file"],
                result["siblings"],
                result["imported_by"],
            )
            return (
                f"Archivo: {result['file']} | "
                f"Funciones hermanas: {result['siblings']} | "
                f"Importado por: {result['imported_by']}"
            )


"""
Uso con el oputput JSON
for entry in json_data:
    graph.add_function(entry['file'], entry['name'], entry['docstring'])
"""
