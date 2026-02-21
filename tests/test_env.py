import chromadb
from neo4j import GraphDatabase
import requests


def test_connections():
    print("--- Verificando Entorno Local ---")

    # 1. Test Ollama
    try:
        res = requests.get(
            "http://localhost:11434/api/tags", timeout=5
        )  # TODO: Usar variables de entorno
        if res.status_code == 200:
            print("✅ Ollama: Online")
    except Exception:
        print("❌ Ollama: Offline (¿Está abierto?)")

    # 2. Test Neo4j
    try:
        driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password123")
        )  # TODO: Usar variables de entorno
        driver.verify_connectivity()
        print("✅ Neo4j: Online y Autenticado")
        driver.close()
    except Exception as e:
        print(f"❌ Neo4j: Error de conexión ({e})")

    # 3. Test ChromaDB
    try:
        # Si usas Docker para Chroma, usa HttpClient. Si no, PersistentClient.
        chromadb.HttpClient(host="localhost", port=8000)
        print("✅ ChromaDB: Online")
    except Exception:
        print("❌ ChromaDB: Offline")


if __name__ == "__main__":
    test_connections()
