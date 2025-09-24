"""
Módulo scraping.py
------------------
Funciones para extraer artículos y guardar resultados en archivos BibTeX.
Autor: [Tu Nombre]
Fecha: 2025-09-23
Descripción: Este módulo contiene funciones para extraer artículos de resultados y guardarlos en archivos .bib.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from utils.bibtex_utils import crear_entrada_bibtex

def extraer_articulos(driver, base):
    """
    Extrae artículos de la página de resultados según la base de datos.
    """
    articulos = []
    if base == "IEEE":
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "xpl-results-item"))
            )
            resultados = driver.find_elements(By.TAG_NAME, "xpl-results-item")
            for resultado in resultados:
                try:
                    titulo = resultado.find_element(By.CSS_SELECTOR, "h3 a").text.strip()
                except:
                    titulo = "Desconocido"
                try:
                    autores = resultado.find_element(By.CSS_SELECTOR, "xpl-authors-name-list p").text.strip()
                except:
                    autores = "Desconocido"
                try:
                    info_publicacion = resultado.find_element(By.CSS_SELECTOR, "div.publisher-info-container").text.strip()
                except:
                    info_publicacion = "Desconocido"
                try:
                    doi_elem = resultado.find_element(By.CSS_SELECTOR, "a[href*='doi.org']")
                    doi = doi_elem.get_attribute("href")
                except:
                    doi = "Sin DOI"
                try:
                    url_art = resultado.find_element(By.CSS_SELECTOR, "h3 a").get_attribute("href")
                except:
                    url_art = "Sin URL"
                articulo = {
                    "Titulo": titulo,
                    "Autores": autores,
                    "Anio": info_publicacion,
                    "DOI": doi,
                    "URL": url_art,
                    "Resumen": "N/A",
                    "Revista": "IEEE",
                    "CitaBib": "",
                    "CitaSCS": ""
                }
                # Descarga de archivos de cita si existen
                if url_art != "Sin URL":
                    ventana_actual = driver.current_window_handle
                    driver.execute_script("window.open(arguments[0]);", url_art)
                    driver.switch_to.window(driver.window_handles[-1])
                    time.sleep(3)
                    try:
                        bib_boton = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '.bib')]"))
                        )
                        bib_link = bib_boton.get_attribute("href")
                        articulo["CitaBib"] = bib_link
                        driver.get(bib_link)
                        time.sleep(2)
                    except Exception:
                        articulo["CitaBib"] = ""
                    try:
                        scs_boton = driver.find_element(By.XPATH, "//a[contains(@href, '.scs')]")
                        scs_link = scs_boton.get_attribute("href")
                        articulo["CitaSCS"] = scs_link
                        driver.get(scs_link)
                        time.sleep(2)
                    except Exception:
                        articulo["CitaSCS"] = ""
                    driver.close()
                    driver.switch_to.window(ventana_actual)
                articulos.append(articulo)
        except Exception as e:
            print(f"[Scraping] IEEE: Error obteniendo resultados: {e}")
    elif base == "ScienceDirect":
        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ResultItem")))
            resultados = driver.find_elements(By.CSS_SELECTOR, ".ResultItem")
            for resultado in resultados:
                try:
                    titulo = resultado.find_element(By.CSS_SELECTOR, "h2").text.strip()
                except Exception as e:
                    titulo = "Desconocido"
                    print(f"[Error] No se pudo extraer el título: {e}")
                try:
                    autores = resultado.find_element(By.CSS_SELECTOR, ".Authors").text.strip()
                except Exception as e:
                    autores = "Desconocido"
                    print(f"[Error] No se pudieron extraer los autores: {e}")
                try:
                    anio = resultado.find_element(By.CSS_SELECTOR, ".Publication-date").text.strip()
                except Exception as e:
                    anio = "Desconocido"
                    print(f"[Error] No se pudo extraer el año: {e}")
                try:
                    doi = resultado.find_element(By.CSS_SELECTOR, ".doi").text.strip()
                except Exception as e:
                    doi = "Sin DOI"
                    print(f"[Error] No se pudo extraer el DOI: {e}")
                try:
                    resumen = resultado.find_element(By.CSS_SELECTOR, ".Abstract").text.strip()
                except Exception as e:
                    resumen = "Sin Resumen"
                    print(f"[Error] No se pudo extraer el resumen: {e}")
                try:
                    url_art = resultado.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                except Exception as e:
                    url_art = "Sin URL"
                    print(f"[Error] No se pudo extraer la URL: {e}")

                articulo = {
                    "Titulo": titulo,
                    "Autores": autores,
                    "Anio": anio,
                    "DOI": doi,
                    "URL": url_art,
                    "Resumen": resumen,
                    "Revista": "ScienceDirect"
                }
                articulos.append(articulo)
        except Exception as e:
            print(f"[Scraping] ScienceDirect: Error obteniendo resultados: {e}")
    elif base == "Nature":
        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app-article-item")))
            resultados = driver.find_elements(By.CSS_SELECTOR, ".app-article-item")
            for resultado in resultados:
                try:
                    titulo = resultado.find_element(By.CSS_SELECTOR, "h3").text.strip()
                except Exception as e:
                    titulo = "Desconocido"
                    print(f"[Error] No se pudo extraer el título: {e}")
                try:
                    autores = resultado.find_element(By.CSS_SELECTOR, ".app-article-author-list").text.strip()
                except Exception as e:
                    autores = "Desconocido"
                    print(f"[Error] No se pudieron extraer los autores: {e}")
                try:
                    anio = resultado.find_element(By.CSS_SELECTOR, ".app-article-meta").text.strip()
                except Exception as e:
                    anio = "Desconocido"
                    print(f"[Error] No se pudo extraer el año: {e}")
                try:
                    doi = resultado.find_element(By.CSS_SELECTOR, ".app-article-doi").text.strip()
                except Exception as e:
                    doi = "Sin DOI"
                    print(f"[Error] No se pudo extraer el DOI: {e}")
                try:
                    resumen = resultado.find_element(By.CSS_SELECTOR, ".app-article-abstract").text.strip()
                except Exception as e:
                    resumen = "Sin Resumen"
                    print(f"[Error] No se pudo extraer el resumen: {e}")
                try:
                    url_art = resultado.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                except Exception as e:
                    url_art = "Sin URL"
                    print(f"[Error] No se pudo extraer la URL: {e}")

                articulo = {
                    "Titulo": titulo,
                    "Autores": autores,
                    "Anio": anio,
                    "DOI": doi,
                    "URL": url_art,
                    "Resumen": resumen,
                    "Revista": "Nature"
                }
                articulos.append(articulo)
        except Exception as e:
            print(f"[Scraping] Nature: Error obteniendo resultados: {e}")
    elif base == "Springer":
        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app-article-item")))
            resultados = driver.find_elements(By.CSS_SELECTOR, ".app-article-item")
            for resultado in resultados:
                try:
                    titulo = resultado.find_element(By.CSS_SELECTOR, "h3").text.strip()
                except Exception as e:
                    titulo = "Desconocido"
                    print(f"[Error] No se pudo extraer el título: {e}")
                try:
                    autores = resultado.find_element(By.CSS_SELECTOR, ".app-article-author-list").text.strip()
                except Exception as e:
                    autores = "Desconocido"
                    print(f"[Error] No se pudieron extraer los autores: {e}")
                try:
                    anio = resultado.find_element(By.CSS_SELECTOR, ".app-article-meta").text.strip()
                except Exception as e:
                    anio = "Desconocido"
                    print(f"[Error] No se pudo extraer el año: {e}")
                try:
                    doi = resultado.find_element(By.CSS_SELECTOR, ".app-article-doi").text.strip()
                except Exception as e:
                    doi = "Sin DOI"
                    print(f"[Error] No se pudo extraer el DOI: {e}")
                try:
                    resumen = resultado.find_element(By.CSS_SELECTOR, ".app-article-abstract").text.strip()
                except Exception as e:
                    resumen = "Sin Resumen"
                    print(f"[Error] No se pudo extraer el resumen: {e}")
                try:
                    url_art = resultado.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                except Exception as e:
                    url_art = "Sin URL"
                    print(f"[Error] No se pudo extraer la URL: {e}")

                articulo = {
                    "Titulo": titulo,
                    "Autores": autores,
                    "Anio": anio,
                    "DOI": doi,
                    "URL": url_art,
                    "Resumen": resumen,
                    "Revista": "Springer"
                }

                # Intentar encontrar enlace .bib
                try:
                    bib_boton = resultado.find_element(By.XPATH, "//a[contains(@href, '.bib')]")
                    bib_link = bib_boton.get_attribute("href")
                    articulo["CitaBib"] = bib_link
                except Exception as e:
                    print(f"[Springer] No se encontró enlace .bib: {e}")
                    articulo["CitaBib"] = ""

                articulos.append(articulo)
        except Exception as e:
            print(f"[Scraping] Springer: Error obteniendo resultados: {e}")
    return articulos

def guardar_articulos_bibtex(articulos, base, termino, carpeta_data="data"):
    """
    Guarda los artículos extraídos en un archivo .bib en la carpeta local 'data'.
    """
    if articulos:
        timestamp = int(time.time() * 1000)
        nombre_archivo = f"{base}_citations_{termino.replace(' ', '_')}_{timestamp}.bib"
        ruta_archivo = os.path.join(os.getcwd(), carpeta_data, nombre_archivo)
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            for articulo in articulos:
                entrada_bib = crear_entrada_bibtex(articulo)
                f.write(entrada_bib)
        print(f"[Scraping] {base}: {len(articulos)} artículos guardados en {ruta_archivo}")
    else:
        print(f"[Scraping] {base}: No se encontraron artículos para el término '{termino}'.")
