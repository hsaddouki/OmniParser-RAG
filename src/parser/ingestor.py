import ast
from pathlib import Path

FUNCTION_DEFINITION = (ast.FunctionDef, ast.AsyncFunctionDef)


# Lee un archivo a partir de una ruta y extrae las funciones en una lista de diccionarios
def extract_functions_from_file(file_path: str) -> list[dict]:
    """Extrae todas las funciones de un archivo de codigo."""
    with Path(file_path).open(encoding="utf-8") as file:
        source = file.read()

    try:
        file_tree = ast.parse(source, filename=file_path)
    except SyntaxError as e:
        print(f"Error al analizar el archivo {file_path}: {e}")
        return []

    functions = []

    for node in ast.walk(file_tree):
        # Comprobamos si el nodo es una definicion de funcion
        if isinstance(node, FUNCTION_DEFINITION):
            args = []
            for arg in node.args.args:
                arg_info = {"name": arg.arg}
                if arg.annotation:
                    arg_info["type"] = ast.unparse(arg.annotation)
                args.append(arg_info)

            # Defaults para argumentos
            defaults = [ast.unparse(d) for d in node.args.defaults]

            # Return type
            return_type = ast.unparse(node.returns) if node.returns else None

            # Decoradores
            decorators = [ast.unparse(d) for d in node.decorator_list]

            # Docstring
            docstring = ast.get_docstring(node)

            # Determinar si es método de clase
            parent_class = None
            for parent in ast.walk(file_tree):
                if isinstance(parent, ast.ClassDef):
                    for item in ast.walk(parent):
                        if item is node:
                            parent_class = parent.name
                            break

            func_info = {
                "name": node.name,
                "type": "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                "file": str(file_path),
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "col_offset": node.col_offset,
                "parent_class": parent_class,
                "decorators": decorators,
                "args": args,
                "defaults": defaults,
                "return_type": return_type,
                "docstring": docstring,
            }
            functions.append(func_info)

    return functions


def analyze_repository(repo_path: str, exclude_dirs: list[str] | None = None) -> dict:
    """Analiza todo el repositorio y retorna metadata de funciones."""
    exclude_dirs = exclude_dirs or [".git", "__pycache__", ".venv", "venv", "node_modules"]
    repo_path = Path(repo_path)

    result = {
        "repository": str(repo_path.resolve()),
        "total_files": 0,
        "total_functions": 0,
        "files": {},
        "functions": [],
    }

    for py_file in repo_path.rglob("*.py"):
        # Excluir directorios no deseados
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue

        relative_path = str(py_file.relative_to(repo_path))
        functions = extract_functions_from_file(py_file)

        result["files"][relative_path] = {
            "path": relative_path,
            "function_count": len(functions),
        }
        result["functions"].extend(functions)
        result["total_files"] += 1

    result["total_functions"] = len(result["functions"])
    return result


def run_ingestor(repo_path: str) -> dict:
    """Ingest a repository: populate the graph and index vectors."""
    from config import settings
    from database.code_graph import CodeGraph
    from database.vector_client import VectorClient

    # 1. Analizamos el repositorio y obtenemos el JSON
    json_data = analyze_repository(repo_path)

    # 2. Poblamos el grafo (Estructura)
    graph = CodeGraph(settings.NEO4J_URI, settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)

    # Iteramos sobre las funciones del repositorio
    for func in json_data["functions"]:
        graph.add_function(func)

    graph.close()  # Cerramos la conexion con la base de datos

    # 3. Indexamos los vectores
    vector_client = VectorClient()
    vector_client.add_code_units(json_data)

    print("Ingesta completada exitosamente")
    return json_data


"""
Ejemplo de uso:
python ingestor.py /ruta/al/repositorio
"""
if __name__ == "__main__":
    import sys

    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    data = run_ingestor(repo)

    print(f"{data['total_files']} archivos analizados")
    print(f"{data['total_functions']} funciones encontradas")
