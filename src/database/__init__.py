"""
database — Connection management for Neo4j and ChromaDB.

This package provides initialised, reusable client objects for the two
persistence backends used by OmniParser-RAG:

- Neo4j client:   manages the Bolt connection, session lifecycle, and
                  Cypher query helpers for the code-relationship graph
                  (class hierarchies, function call graphs, module
                  dependencies).
- ChromaDB client: manages the local persistent vector store, collection
                   creation, embedding upserts, and similarity queries
                   used by the retrieval layer.

All connection parameters are read from environment variables (see
.env.example for the full list).
"""
