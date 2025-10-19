import bibtexparser
import os

# Ruta a la carpeta de tus datos
data_folder = "data"

# Listar todos los archivos .bib
for file in os.listdir(data_folder):
    if file.endswith(".bib"):
        file_path = os.path.join(data_folder, file)
        print(f"\n📘 Leyendo archivo: {file}")

        with open(file_path, encoding="utf-8") as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)

            # Mostrar cuántas entradas hay
            print(f"  → Entradas encontradas: {len(bib_database.entries)}")

            # Mostrar las primeras 2 para verificar
            for entry in bib_database.entries[:2]:
                title = entry.get("title", "Sin título")
                author = entry.get("author", "Sin autor")
                abstract = entry.get("abstract", "Sin resumen")
                print(f"\nTítulo: {title}\nAutor(es): {author}\nResumen: {abstract[:150]}...")


