import os
from pathlib import Path

# Base del proyecto (carpeta donde está este script)
BASE_DIR = Path(__file__).resolve().parent

# 📁 Ruta relativa a la carpeta "data"
carpeta = str(BASE_DIR / "data")

# 📄 Archivo de salida en productosUnificados/productosUnificados.txt (se crea la carpeta si no existe)
output_dir = BASE_DIR / "productosUnificados"
output_dir.mkdir(parents=True, exist_ok=True)
archivo_salida = str(output_dir / "productosUnificados.txt")

# Lista para guardar el contenido
archivos = [os.path.join(carpeta, f) for f in os.listdir(carpeta) if os.path.isfile(os.path.join(carpeta, f))]

# 🔁 Unificar todo el contenido en un solo archivo
with open(archivo_salida, 'w', encoding='utf-8') as salida:
    for archivo in archivos:
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                salida.write(f"\n===== CONTENIDO DEL ARCHIVO: {os.path.basename(archivo)} =====\n\n")
                salida.write(f.read())
                salida.write("\n\n")
        except Exception as e:
            print(f"No se pudo leer el archivo {archivo}: {e}")

print(f"✅ Se unificaron {len(archivos)} archivos en '{archivo_salida}'")
