import logging

from langchain_ollama import OllamaLLM

from config import settings
from utils import trace

logger = logging.getLogger("omniparser.llm_client")

PROMPT_TEMPLATE = """
Eres un Arquitecto de Software Senior. Basándote en el siguiente contexto de código
extraído de un Grafo de Conocimiento y una base de datos vectorial, responde a la pregunta.

CONTEXTO:
{context}

PREGUNTA:
{question}

INSTRUCCIÓN: Si no estás seguro, admítelo. Si sugieres cambios, explica a qué otras
funciones afectará basándote en las relaciones del grafo.
"""


class LLMClient:
    """Sends a question + retrieved context to the local Ollama LLM."""

    def __init__(self, retriever) -> None:
        self.retriever = retriever
        self.llm = OllamaLLM(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
        )

    @trace
    def ask(self, question: str, top_k: int = settings.VECTOR_SEARCH_TOP_K) -> str:
        """Retrieve context and ask the LLM, returning its response."""
        context = self.retriever.retrieve_context(question, k=top_k)
        prompt = PROMPT_TEMPLATE.format(context=context, question=question)
        logger.info("Sending prompt to Ollama model: %s", settings.OLLAMA_MODEL)
        return self.llm.invoke(prompt)
