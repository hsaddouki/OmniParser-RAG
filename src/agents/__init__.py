"""
agents — LangGraph orchestration layer.

This package contains the LangGraph state machines that drive the four
core workflows of OmniParser-RAG:

- Ingestion loop:   parse source code → embed chunks → store in ChromaDB
                    and Neo4j → index relationships.
- Retrieval loop:   run parallel vector search (ChromaDB) and graph
                    traversal (Neo4j) → merge and rank results.
- Generation loop:  pass retrieved context to the local LLM (Ollama) →
                    produce code or analysis.
- Self-correction loop: validate generated output for syntax/logic errors
                        → retry with adjusted context on failure (up to
                        SELF_CORRECTION_MAX_RETRIES attempts).
"""
