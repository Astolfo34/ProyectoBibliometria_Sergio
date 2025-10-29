from pathlib import Path
import os
from typing import Optional


def unificar(carpeta_data: Optional[str] = None, salida_path: Optional[str] = None) -> str:
    """
    Unifica todos los archivos de texto de la carpeta data/ en un único archivo
    productosUnificados/productosUnificados.txt, preservando el nombre de cada
    archivo como encabezado.

    - carpeta_data: ruta de la carpeta con los .bib/.txt a unificar. Por defecto, <repo>/data
    - salida_path: ruta completa del archivo de salida. Por defecto, <repo>/productosUnificados/productosUnificados.txt

    Devuelve la ruta del archivo de salida generado.
    """
    # Raíz del repositorio (subir un nivel desde utils/)
    repo_root = Path(__file__).resolve().parents[1]

    data_dir = Path(carpeta_data) if carpeta_data else (repo_root / "data")
    salida = Path(salida_path) if salida_path else (repo_root / "productosUnificados" / "productosUnificados.txt")
    salida.parent.mkdir(parents=True, exist_ok=True)

    if not data_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta de datos: {data_dir}")

    archivos = [p for p in data_dir.iterdir() if p.is_file()]

    with open(salida, 'w', encoding='utf-8') as out:
        for archivo in archivos:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    out.write(f"\n===== CONTENIDO DEL ARCHIVO: {archivo.name} =====\n\n")
                    out.write(f.read())
                    out.write("\n\n")
            except Exception as e:
                print(f"No se pudo leer el archivo {archivo}: {e}")

    print(f"✅ Se unificaron {len(archivos)} archivos en '{salida}'")
    return str(salida)


if __name__ == "__main__":
    unificar()
