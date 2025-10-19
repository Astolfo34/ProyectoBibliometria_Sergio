import os
import bibtexparser
import pandas as pd

def load_bib_data(data_folder="data"):
    registros = []

    for file in os.listdir(data_folder):
        if file.endswith(".bib"):
            path = os.path.join(data_folder, file)
            with open(path, encoding="utf-8") as bibtex_file:
                bib_database = bibtexparser.load(bibtex_file)

                for entry in bib_database.entries:
                    title = entry.get("title", "").strip()
                    authors = entry.get("author", "").replace("\n", " ").strip()
                    abstract = entry.get("abstract", "").strip()

                    if title:  # Evita entradas vacías
                        registros.append({
                            "archivo": file,
                            "titulo": title,
                            "autores": authors,
                            "resumen": abstract
                        })

    return pd.DataFrame(registros)
