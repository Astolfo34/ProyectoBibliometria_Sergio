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
    if autor and autor.strip():
        primer_autor = autor.split()[0]
    else:
        primer_autor = "Desconocido"
    return f"{primer_autor}{anio}"

def crear_entrada_bibtex(entrada):
    """
    Crea una entrada BibTeX a partir de un diccionario de metadatos.
    :param entrada: Diccionario con los campos del artículo.
    :return: Cadena con la entrada BibTeX.
    """
    clave_bib = generar_clave_bibtex(entrada.get("Autores", "Desconocido"), entrada.get("Anio", "Desconocido"))
    bibtex = f"@article{{{clave_bib},\n"
    bibtex += f"  author = {{{entrada.get('Autores', 'Desconocido')}}},\n"
    bibtex += f"  title = {{{entrada.get('Titulo', 'Desconocido')}}},\n"
    bibtex += f"  year = {{{entrada.get('Anio', 'Desconocido')}}},\n"
    if entrada.get("Revista"):
        bibtex += f"  journal = {{{entrada.get('Revista')}}},\n"
    if entrada.get("DOI") and entrada.get("DOI") != "Sin DOI":
        bibtex += f"  doi = {{{entrada.get('DOI')}}},\n"
    if entrada.get("URL") and entrada.get("URL") != "Sin URL":
        bibtex += f"  url = {{{entrada.get('URL')}}},\n"
    if entrada.get("Resumen") and entrada.get("Resumen") != "N/A":
        bibtex += f"  abstract = {{{entrada.get('Resumen')}}},\n"
    if entrada.get("CitaBib"):
        bibtex += f"  citation_bib = {{{entrada.get('CitaBib')}}},\n"
    if entrada.get("CitaSCS"):
        bibtex += f"  citation_scs = {{{entrada.get('CitaSCS')}}},\n"
    bibtex += "}\n\n"
    return bibtex
