from neo4j import GraphDatabase


class CodeGraph:
    """Manages code relationship data in a Neo4j graph database."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        self.driver.close()

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

    def add_import(self, source_file: str, target_file: str) -> None:
        """Create an IMPORTS relationship between two File nodes."""
        with self.driver.session() as session:
            query = """
            MERGE (src:File {name: $source})
            MERGE (tgt:File {name: $target})
            MERGE (src)-[:IMPORTS]->(tgt)
            """
            session.run(query, source=source_file, target=target_file)


"""
Uso con el oputput JSON
for entry in json_data:
    graph.add_function(entry['file'], entry['name'], entry['docstring'])
"""
