from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import chromadb
from neo4j import GraphDatabase
import requests

from config import settings


def test_connections():
    print("--- Verificando Entorno Local ---")

    # 1. Test Ollama
    try:
        res = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if res.status_code == 200:
            print("✅ Ollama: Online")
    except Exception:
        print("❌ Ollama: Offline (¿Está abierto?)")

    # 2. Test Neo4j
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI, auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
        print("✅ Neo4j: Online y Autenticado")
        driver.close()
    except Exception as e:
        print(f"❌ Neo4j: Error de conexión ({e})")

    # 3. Test ChromaDB
    try:
        # Si usas Docker para Chroma, usa HttpClient. Si no, PersistentClient.
        chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        print("✅ ChromaDB: Online")
    except Exception:
        print("❌ ChromaDB: Offline")


if __name__ == "__main__":
    test_connections()
