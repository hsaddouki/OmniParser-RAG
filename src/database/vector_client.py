from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from config import settings


class VectorClient:
    """ChromaDB-backed vector store for semantic code search."""

    def __init__(self, collection_name: str = settings.CHROMA_COLLECTION_NAME) -> None:
        # 1. Configuramos el motor de embeddings local (Ollama)
        self.embeddings = OllamaEmbeddings(model=settings.OLLAMA_EMBEDDING_MODEL)

        # 2. Persistencia en disco (carpeta data/chroma)
        self.vector_db = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=settings.CHROMA_PERSIST_PATH,
        )

    def add_code_units(self, json_data: dict) -> None:
        """Convierte tu JSON en Documentos de LangChain y los indexa."""
        documents = []
        for entry in json_data:
            # El contenido que queremos vectorizar es el docstring + nombre
            content = f"Función: {entry['name']}\nDescripción: {entry.get('docstring') or ''}"

            # Los metadatos son cruciales para filtrar después
            metadata = {"file": entry["file"], "name": entry["name"], "line": entry["line_start"]}

            documents.append(Document(page_content=content, metadata=metadata))

        self.vector_db.add_documents(documents)
        print(f"{len(documents)} unidades de código indexadas en ChromaDB.")

    def search(self, query: str, k: int = 3) -> list[Document]:
        """Busca las k unidades de código más similares semánticamente."""
        return self.vector_db.similarity_search(query, k=k)
