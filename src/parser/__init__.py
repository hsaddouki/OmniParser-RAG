"""
parser — Code parsing and structure extraction pipeline.

This package is responsible for transforming raw source files into the
structured representations consumed by the ingestion layer:

- AST-based analysis (via `astroid`) for Python-specific semantics:
  class definitions, method signatures, imports, and docstrings.
- Tree-sitter parsing for language-agnostic, incremental syntax trees
  across multiple target languages.
- Chunking: splits large files into semantically meaningful units
  (functions, classes, top-level blocks) before embedding.
- Relationship extraction: identifies inter-module imports, inheritance
  chains, and function call sites to feed into the Neo4j graph.
"""
