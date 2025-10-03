"""
Módulo bibtex_utils.py
----------------------
Funciones utilitarias para la generación de claves y entradas BibTeX.
Autor: [Tu Nombre]
Fecha: 2025-09-23
Descripción: Este módulo contiene funciones para crear claves y entradas BibTeX a partir de metadatos de artículos científicos.
"""

def generar_clave_bibtex(autor, anio):
    """
    Genera una clave BibTeX a partir del primer autor y el año.
    :param autor: Nombre(s) del autor principal.
    :param anio: Año de publicación.
    :return: Clave BibTeX única.
    """
    if autor and autor.strip() and autor != "Autores no disponibles":
        # Extraer el apellido del primer autor
        primer_autor = autor.split(",")[0].split(";")[0].strip()
        # Limpiar caracteres especiales y obtener solo el apellido
        primer_autor = primer_autor.split()[-1] if primer_autor.split() else "Desconocido"
        # Remover caracteres especiales
        import re
        primer_autor = re.sub(r'[^a-zA-Z]', '', primer_autor)
    else:
        primer_autor = "Desconocido"
    
    # Limpiar el año
    if anio and anio != "Año no disponible":
        import re
        year_match = re.search(r'20\d{2}|19\d{2}', str(anio))
        anio_limpio = year_match.group(0) if year_match else "2024"
    else:
        anio_limpio = "2024"
    
    return f"{primer_autor}{anio_limpio}"

def crear_entrada_bibtex(entrada):
    """
    Crea una entrada BibTeX a partir de un diccionario de metadatos.
    :param entrada: Diccionario con los campos del artículo.
    :return: Cadena con la entrada BibTeX.
    """
    # Generar clave BibTeX única
    clave_bib = generar_clave_bibtex(entrada.get("Autores", "Desconocido"), entrada.get("Anio", "Desconocido"))
    
    # Determinar el tipo de entrada
    tipo_entrada = entrada.get("Tipo", "article")
    
    # Iniciar la entrada BibTeX
    bibtex = f"@{tipo_entrada}{{{clave_bib},\n"
    
    # Campos obligatorios
    if entrada.get("Titulo") and entrada.get("Titulo") != "Título no disponible":
        titulo = entrada.get("Titulo").replace("{", "").replace("}", "")
        bibtex += f"  title = {{{titulo}}},\n"
    
    if entrada.get("Autores") and entrada.get("Autores") != "Autores no disponibles":
        autores = entrada.get("Autores").replace("{", "").replace("}", "")
        bibtex += f"  author = {{{autores}}},\n"
    
    if entrada.get("Anio") and entrada.get("Anio") != "Año no disponible":
        import re
        year_match = re.search(r'20\d{2}|19\d{2}', str(entrada.get("Anio")))
        anio = year_match.group(0) if year_match else "2024"
        bibtex += f"  year = {{{anio}}},\n"
    
    # Campos opcionales
    if entrada.get("Revista") and entrada.get("Revista") not in ["IEEE", "ScienceDirect", "Springer"]:
        revista = entrada.get("Revista").replace("{", "").replace("}", "")
        bibtex += f"  journal = {{{revista}}},\n"
    elif entrada.get("Revista") in ["IEEE", "ScienceDirect", "Springer"]:
        bibtex += f"  publisher = {{{entrada.get('Revista')}}},\n"
    
    if entrada.get("DOI") and entrada.get("DOI") != "DOI no disponible":
        doi = entrada.get("DOI")
        if doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")
        bibtex += f"  doi = {{{doi}}},\n"
    
    if entrada.get("URL") and entrada.get("URL") != "URL no disponible":
        bibtex += f"  url = {{{entrada.get('URL')}}},\n"
    
    if entrada.get("Resumen") and entrada.get("Resumen") not in ["Resumen no disponible", "N/A", "Sin Resumen"]:
        resumen = entrada.get("Resumen").replace("{", "").replace("}", "")
        # Limitar el resumen a 500 caracteres para evitar entradas muy largas
        if len(resumen) > 500:
            resumen = resumen[:497] + "..."
        bibtex += f"  abstract = {{{resumen}}},\n"
    
    # Campos específicos de scraping (si existen)
    if entrada.get("CitaBib"):
        bibtex += f"  note = {{Citation BibTeX: {entrada.get('CitaBib')}}},\n"
    
    # Remover la última coma y cerrar la entrada
    bibtex = bibtex.rstrip(",\n") + "\n"
    bibtex += "}\n\n"
    
    return bibtex
