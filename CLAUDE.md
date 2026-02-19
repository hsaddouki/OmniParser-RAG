# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OmniParser-RAG is a code analysis and generation system combining local LLM inference with a hybrid GraphRAG retrieval architecture. The system is designed to be fully local (no external API calls).

## Planned Technology Stack

- **Local LLM**: Ollama with Llama 3.1 or DeepSeek-Coder models
- **Vector Store**: ChromaDB for semantic/embedding-based retrieval
- **Graph Store**: Neo4j for code relationship modeling (class hierarchies, function dependencies)
- **Language**: Python (expected primary language)

## Architecture

The system uses a hybrid retrieval approach:

1. **Ingestion**: Parse source code, extract structure (classes, functions, dependencies), store embeddings in ChromaDB and relationships in Neo4j
2. **Retrieval**: On a query, run parallel vector search (ChromaDB) and graph traversal (Neo4j), then merge results
3. **Generation**: Pass retrieved context to local LLM via Ollama for code generation/analysis
4. **Self-Correcting Loop**: Validate generated code for syntax/logic errors; retry with adjusted context on failure

Key capabilities:
- **Code Topology Awareness**: Navigate class hierarchies and function dependency graphs natively
- **GraphRAG**: Combines semantic similarity (vector) with structural relationships (graph) for richer context

## Project Status

Pre-implementation phase. No source code exists yet — only this documentation. When implementing:
- Set up Python project structure (`pyproject.toml` or `requirements.txt`)
- External services required: Ollama (running locally), Neo4j instance, ChromaDB
- Ollama must have the target model pulled before inference (`ollama pull llama3.1` or `ollama pull deepseek-coder`)
