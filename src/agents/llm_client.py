import logging

from langchain_ollama import OllamaLLM

from config import settings
from utils import trace

logger = logging.getLogger("omniparser.llm_client")

PROMPT_TEMPLATE = """
You are a Senior Software Architect. Based on the following code context extracted
from a Knowledge Graph and a vector database, answer the question.

CONTEXT:
{context}

QUESTION:
{question}

INSTRUCTION: If you are unsure, admit it. If you suggest changes, explain which other
functions will be affected based on the graph relationships.
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
