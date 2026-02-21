from neo4j import GraphDatabase

class CodeGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_function(self, file_name, func_name, docstring):
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