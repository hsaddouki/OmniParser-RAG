from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

class VectorClient:
    def __init__(self, collection_name="code_base"):
        # 1. Configuramos el motor de embeddings local (Ollama)
        self.embeddings = OllamaEmbeddings(model="mxbai-embed-large") # TODO: Cambiar por una variable de entorno configurable
        
        # 2. Persistencia en disco (carpeta data/chroma)
        self.vector_db = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory="./data/chroma_db"
        )

    def add_code_units(self, json_data):
        """
        Convierte tu JSON en Documentos de LangChain y los indexa.
        """
        documents = []
        for entry in json_data:
            # El contenido que queremos vectorizar es el docstring + nombre
            content = f"Función: {entry['name']}\nDescripción: {entry['docstring']}"
            
            # Los metadatos son cruciales para filtrar después
            metadata = {
                "file": entry['file'],
                "name": entry['name'],
                "line": entry['line']
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        self.vector_db.add_documents(documents)
        print(f"{len(documents)} unidades de código indexadas en ChromaDB.")

    def search(self, query, k=3):
        """
        Busca las k unidades de código más similares semánticamente.
        """
        results = self.vector_db.similarity_search(query, k=k)
        return results