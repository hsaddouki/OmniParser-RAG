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
            MERGE (fn:Function {name: $func_name})
            SET fn.docstring = $docstring
            MERGE (f)-[:CONTAINS]->(fn)
            """
            session.run(query, file_name=file_name, func_name=func_name, docstring=docstring)


"""
Uso con el oputput JSON
for entry in json_data:
    graph.add_function(entry['file'], entry['name'], entry['docstring'])
"""
