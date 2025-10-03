"""
Funciones para extraer artículos y guardar resultados en archivos BibTeX.
Descripción: Este módulo contiene funciones para extraer artículos de resultados y guardarlos en archivos .bib.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import re
from utils.bibtex_utils import crear_entrada_bibtex

def extraer_articulos(driver, base, max_resultados=1000):
    """
    Extrae artículos de la página de resultados según la base de datos.
    Extrae hasta max_resultados artículos (por defecto 1000).
    """
    articulos = []
    print(f"[Scraping] {base}: Iniciando extracción de hasta {max_resultados} artículos...")
    
    if base == "IEEE":
        try:
            # Esperar a que aparezcan los resultados
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "xpl-results-item"))
            )
            
            # Intentar cargar más resultados mediante scroll
            for i in range(5):  # Hacer scroll para cargar más resultados
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            resultados = driver.find_elements(By.TAG_NAME, "xpl-results-item")
            print(f"[IEEE] Encontrados {len(resultados)} elementos de resultado")
            
            count = 0
            for resultado in resultados[:max_resultados]:
                if count >= max_resultados:
                    break
                    
                try:
                    # Extraer título
                    titulo_elem = resultado.find_element(By.CSS_SELECTOR, "h3 a, .document-title a, .result-item-title a")
                    titulo = titulo_elem.text.strip()
                except Exception as e:
                    print(f"[IEEE] Error extrayendo título: {e}")
                    titulo = "Título no disponible"
                
                try:
                    # Extraer autores - múltiples selectores
                    autores_elem = resultado.find_element(By.CSS_SELECTOR, "xpl-authors-name-list p, .authors, .author-list")
                    autores = autores_elem.text.strip()
                except Exception as e:
                    print(f"[IEEE] Error extrayendo autores: {e}")
                    autores = "Autores no disponibles"
                
                try:
                    # Extraer año de publicación
                    info_pub = resultado.find_element(By.CSS_SELECTOR, "div.publisher-info-container, .publication-year, .date-published")
                    info_texto = info_pub.text.strip()
                    # Extraer año del texto
                    import re
                    year_match = re.search(r'20\d{2}|19\d{2}', info_texto)
                    anio = year_match.group(0) if year_match else "Año no disponible"
                except Exception as e:
                    print(f"[IEEE] Error extrayendo año: {e}")
                    anio = "Año no disponible"
                
                try:
                    # Extraer DOI
                    doi_elem = resultado.find_element(By.CSS_SELECTOR, "a[href*='doi.org'], .doi-link")
                    doi = doi_elem.get_attribute("href")
                    if not doi.startswith("http"):
                        doi = f"https://doi.org/{doi}"
                except Exception as e:
                    doi = "DOI no disponible"
                
                try:
                    # Extraer URL del artículo
                    url_elem = resultado.find_element(By.CSS_SELECTOR, "h3 a, .document-title a, .result-item-title a")
                    url_art = url_elem.get_attribute("href")
                    if url_art and not url_art.startswith("http"):
                        url_art = f"https://ieeexplore.ieee.org{url_art}"
                except Exception as e:
                    url_art = "URL no disponible"
                
                try:
                    # Extraer revista/conferencia
                    revista_elem = resultado.find_element(By.CSS_SELECTOR, ".publication-title, .publisher-info, .conference-name")
                    revista = revista_elem.text.strip()
                except Exception as e:
                    revista = "IEEE"
                
                try:
                    # Extraer resumen si está disponible
                    resumen_elem = resultado.find_element(By.CSS_SELECTOR, ".abstract-text, .summary")
                    resumen = resumen_elem.text.strip()
                except Exception as e:
                    resumen = "Resumen no disponible"
                
                articulo = {
                    "Titulo": titulo,
                    "Autores": autores,
                    "Anio": anio,
                    "DOI": doi,
                    "URL": url_art,
                    "Resumen": resumen,
                    "Revista": revista,
                    "Tipo": "article"
                }
                
                articulos.append(articulo)
                count += 1
                print(f"[IEEE] Artículo {count}: {titulo[:50]}...")
                
        except Exception as e:
            print(f"[Scraping] IEEE: Error obteniendo resultados: {e}")
    elif base == "ScienceDirect":
        try:
            print(f"[ScienceDirect] Iniciando extracción masiva de hasta {max_resultados} artículos...")
            
            # Función auxiliar para cargar más resultados
            def cargar_mas_resultados_sciencedirect():
                try:
                    # Cambiar a mostrar 100 resultados por página
                    enlaces_100 = driver.find_elements(By.CSS_SELECTOR, "a[href*='show=100']")
                    if enlaces_100:
                        print("[ScienceDirect] Cambiando a 100 resultados por página...")
                        driver.execute_script("arguments[0].click();", enlaces_100[0])
                        time.sleep(3)
                    
                    # Hacer scroll para cargar contenido dinámico
                    for i in range(10):
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                        
                    return True
                except Exception as e:
                    print(f"[ScienceDirect] Error cargando más resultados: {e}")
                    return False
            
            # Cargar más resultados inicialmente
            cargar_mas_resultados_sciencedirect()
            
            # Extraer página por página
            pagina_actual = 1
            total_extraidos = 0
            max_paginas = 40  # Limitar a 40 páginas para evitar bucles infinitos
            
            while total_extraidos < max_resultados and pagina_actual <= max_paginas:
                print(f"[ScienceDirect] Procesando página {pagina_actual}...")
                
                # Esperar a que aparezcan los resultados con múltiples selectores
                try:
                    WebDriverWait(driver, 30).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".ResultItem")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, "li.ResultItem")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".result-item-container"))
                        )
                    )
                except Exception as e:
                    print(f"[ScienceDirect] No se pudieron cargar resultados en página {pagina_actual}: {e}")
                    break
                
                # Buscar elementos de resultado con selectores múltiples
                resultados = driver.find_elements(By.CSS_SELECTOR, ".ResultItem, li.ResultItem, .result-item-container")
                if not resultados:
                    # Intentar con selectores alternativos
                    resultados = driver.find_elements(By.CSS_SELECTOR, "[data-doi], .search-result-wrapper li")
                
                print(f"[ScienceDirect] Encontrados {len(resultados)} elementos en página {pagina_actual}")
                
                if not resultados:
                    print(f"[ScienceDirect] No se encontraron más resultados en página {pagina_actual}")
                    break
                
                # Procesar cada resultado
                for idx, resultado in enumerate(resultados):
                    if total_extraidos >= max_resultados:
                        break
                    
                    try:
                        # Extraer DOI desde el atributo data-doi o desde enlaces
                        doi = ""
                        try:
                            doi = resultado.get_attribute("data-doi")
                            if not doi:
                                doi_links = resultado.find_elements(By.CSS_SELECTOR, "a[href*='doi.org'], [data-doi]")
                                if doi_links:
                                    doi = doi_links[0].get_attribute("href") or doi_links[0].get_attribute("data-doi")
                        except:
                            pass
                        
                        # Extraer título con múltiples selectores
                        titulo = "Título no disponible"
                        try:
                            titulo_selectors = [
                                "h2 a.result-list-title-link",
                                "h2 a",
                                ".result-list-title-link",
                                "h2",
                                "a[id*='title-']",
                                ".anchor-text"
                            ]
                            for selector in titulo_selectors:
                                titulo_elem = resultado.find_element(By.CSS_SELECTOR, selector)
                                if titulo_elem and titulo_elem.text.strip():
                                    titulo = titulo_elem.text.strip()
                                    break
                        except Exception as e:
                            print(f"[ScienceDirect] Error extrayendo título en resultado {idx+1}: {e}")
                        
                        # Extraer autores
                        autores = "Autores no disponibles"
                        try:
                            autores_selectors = [
                                ".Authors .author",
                                "ol.Authors li .author",
                                ".author",
                                "[class*='author']"
                            ]
                            for selector in autores_selectors:
                                autores_elems = resultado.find_elements(By.CSS_SELECTOR, selector)
                                if autores_elems:
                                    autores_list = [elem.text.strip() for elem in autores_elems if elem.text.strip()]
                                    if autores_list:
                                        autores = ", ".join(autores_list)
                                        break
                        except Exception as e:
                            print(f"[ScienceDirect] Error extrayendo autores: {e}")
                        
                        # Extraer año de publicación
                        anio = "Año no disponible"
                        try:
                            fecha_selectors = [
                                ".SubType .srctitle-date-fields span:last-child",
                                ".srctitle-date-fields span:last-child",
                                "[class*='date']",
                                ".SubType span"
                            ]
                            for selector in fecha_selectors:
                                fecha_elem = resultado.find_element(By.CSS_SELECTOR, selector)
                                if fecha_elem and fecha_elem.text.strip():
                                    fecha_texto = fecha_elem.text.strip()
                                    import re
                                    year_match = re.search(r'20\d{2}|19\d{2}', fecha_texto)
                                    if year_match:
                                        anio = year_match.group(0)
                                        break
                        except Exception as e:
                            print(f"[ScienceDirect] Error extrayendo año: {e}")
                        
                        # Extraer URL del artículo
                        url_art = "URL no disponible"
                        try:
                            url_selectors = [
                                "h2 a.result-list-title-link",
                                "h2 a",
                                ".result-list-title-link",
                                "a[href*='/science/article/']"
                            ]
                            for selector in url_selectors:
                                url_elem = resultado.find_element(By.CSS_SELECTOR, selector)
                                if url_elem:
                                    url_art = url_elem.get_attribute("href")
                                    if url_art and url_art.startswith("/"):
                                        url_art = f"https://www.sciencedirect.com{url_art}"
                                    break
                        except Exception as e:
                            print(f"[ScienceDirect] Error extrayendo URL: {e}")
                        
                        # Extraer revista/fuente
                        revista = "ScienceDirect"
                        try:
                            revista_selectors = [
                                ".SubType .subtype-srctitle-link",
                                ".subtype-srctitle-link",
                                "a[href*='/science/book/'], a[href*='/journal/']"
                            ]
                            for selector in revista_selectors:
                                revista_elem = resultado.find_element(By.CSS_SELECTOR, selector)
                                if revista_elem and revista_elem.text.strip():
                                    revista = revista_elem.text.strip()
                                    # Limpiar etiquetas HTML como <em>
                                    revista = re.sub(r'<[^>]+>', '', revista)
                                    break
                        except Exception as e:
                            print(f"[ScienceDirect] Error extrayendo revista: {e}")
                        
                        # Extraer tipo de artículo
                        tipo_articulo = "article"
                        try:
                            tipo_elem = resultado.find_element(By.CSS_SELECTOR, ".article-type, [class*='article-type']")
                            if tipo_elem and "chapter" in tipo_elem.text.lower():
                                tipo_articulo = "incollection"
                        except:
                            pass
                        
                        # Intentar extraer resumen (si está disponible)
                        resumen = "Resumen no disponible"
                        try:
                            resumen_elem = resultado.find_element(By.CSS_SELECTOR, ".abstract, .Abstract, .summary")
                            if resumen_elem and resumen_elem.text.strip():
                                resumen = resumen_elem.text.strip()
                        except:
                            pass
                        
                        # Validar que tenemos datos mínimos
                        if titulo == "Título no disponible":
                            continue
                        
                        # Crear entrada del artículo
                        articulo = {
                            "Titulo": titulo,
                            "Autores": autores,
                            "Anio": anio,
                            "DOI": doi if doi else "DOI no disponible",
                            "URL": url_art,
                            "Resumen": resumen,
                            "Revista": revista,
                            "Tipo": tipo_articulo
                        }
                        
                        articulos.append(articulo)
                        total_extraidos += 1
                        
                        print(f"[ScienceDirect] Artículo {total_extraidos}: {titulo[:60]}...")
                        
                    except Exception as e:
                        print(f"[ScienceDirect] Error procesando resultado {idx+1}: {e}")
                        continue
                
                # Intentar ir a la siguiente página
                if total_extraidos < max_resultados:
                    try:
                        # Buscar enlace de "siguiente página" o botón de paginación
                        next_links = driver.find_elements(By.CSS_SELECTOR, 
                            "a[aria-label*='next'], a[href*='offset='], .pagination a:last-child, a[href*='&page=']")
                        
                        siguiente_encontrado = False
                        for link in next_links:
                            if ("next" in link.get_attribute("aria-label").lower() or 
                                "siguiente" in link.text.lower() or
                                int(re.search(r'\d+', link.text or "0").group(0) or 0) > pagina_actual):
                                print(f"[ScienceDirect] Navegando a página {pagina_actual + 1}...")
                                driver.execute_script("arguments[0].click();", link)
                                time.sleep(5)
                                siguiente_encontrado = True
                                break
                        
                        if not siguiente_encontrado:
                            print(f"[ScienceDirect] No se encontró enlace a siguiente página")
                            break
                        
                        pagina_actual += 1
                        
                    except Exception as e:
                        print(f"[ScienceDirect] Error navegando a siguiente página: {e}")
                        break
                else:
                    break
                    
        except Exception as e:
            print(f"[Scraping] ScienceDirect: Error general obteniendo resultados: {e}")

    elif base == "Springer":
        try:
            print(f"[Springer] Iniciando extracción masiva de hasta {max_resultados} artículos...")
            
            # Función auxiliar para cargar más resultados
            def cargar_mas_resultados_springer():
                try:
                    # Hacer scroll para cargar contenido dinámico
                    for i in range(10):
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                    return True
                except Exception as e:
                    print(f"[Springer] Error cargando más resultados: {e}")
                    return False
            
            # Cargar más resultados inicialmente
            cargar_mas_resultados_springer()
            
            # Extraer página por página
            pagina_actual = 1
            total_extraidos = 0
            max_paginas = 50  # Limitar a 50 páginas para evitar bucles infinitos
            
            while total_extraidos < max_resultados and pagina_actual <= max_paginas:
                print(f"[Springer] Procesando página {pagina_actual}...")
                
                # Esperar a que aparezcan los resultados con selectores específicos de Springer
                try:
                    WebDriverWait(driver, 30).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "li.app-card-open")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='search-result-item']")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, "ol[data-test='darwin-search'] li"))
                        )
                    )
                except Exception as e:
                    print(f"[Springer] No se pudieron cargar resultados en página {pagina_actual}: {e}")
                    break
                
                # Buscar elementos de resultado con selectores específicos de Springer
                resultados = driver.find_elements(By.CSS_SELECTOR, "li.app-card-open[data-test='search-result-item']")
                if not resultados:
                    # Selectores alternativos
                    resultados = driver.find_elements(By.CSS_SELECTOR, "li[data-test='search-result-item'], ol[data-test='darwin-search'] li")
                
                print(f"[Springer] Encontrados {len(resultados)} elementos en página {pagina_actual}")
                
                if not resultados:
                    print(f"[Springer] No se encontraron más resultados en página {pagina_actual}")
                    break
                
                # Procesar cada resultado
                for idx, resultado in enumerate(resultados):
                    if total_extraidos >= max_resultados:
                        break
                    
                    try:
                        # Extraer título
                        titulo = "Título no disponible"
                        try:
                            titulo_selectors = [
                                "h3.app-card-open__heading a span",
                                "h3.app-card-open__heading a",
                                "h3 a span",
                                "h3 a",
                                "[data-test='title'] a span",
                                "[data-test='title'] a"
                            ]
                            for selector in titulo_selectors:
                                titulo_elem = resultado.find_element(By.CSS_SELECTOR, selector)
                                if titulo_elem and titulo_elem.text.strip():
                                    titulo = titulo_elem.text.strip()
                                    break
                        except Exception as e:
                            print(f"[Springer] Error extrayendo título en resultado {idx+1}: {e}")
                        
                        # Extraer autores
                        autores = "Autores no disponibles"
                        try:
                            autores_selectors = [
                                ".app-card-open__authors [data-test='authors']",
                                "[data-test='authors']",
                                ".app-author-list span[data-test='authors']",
                                ".app-card-open__authors span"
                            ]
                            for selector in autores_selectors:
                                autores_elem = resultado.find_element(By.CSS_SELECTOR, selector)
                                if autores_elem and autores_elem.text.strip():
                                    autores = autores_elem.text.strip()
                                    break
                        except Exception as e:
                            print(f"[Springer] Error extrayendo autores: {e}")
                        
                        # Extraer año de publicación
                        anio = "Año no disponible"
                        try:
                            fecha_selectors = [
                                ".app-card-open__meta [data-test='published']",
                                "[data-test='published']",
                                ".c-meta__item[data-test='published']",
                                ".app-card-open__meta .c-meta__item"
                            ]
                            for selector in fecha_selectors:
                                fecha_elem = resultado.find_element(By.CSS_SELECTOR, selector)
                                if fecha_elem and fecha_elem.text.strip():
                                    fecha_texto = fecha_elem.text.strip()
                                    import re
                                    year_match = re.search(r'20\d{2}|19\d{2}', fecha_texto)
                                    if year_match:
                                        anio = year_match.group(0)
                                        break
                        except Exception as e:
                            print(f"[Springer] Error extrayendo año: {e}")
                        
                        # Extraer DOI desde la URL del artículo
                        doi = "DOI no disponible"
                        url_art = "URL no disponible"
                        try:
                            url_selectors = [
                                "h3.app-card-open__heading a.app-card-open__link",
                                "h3 a.app-card-open__link",
                                "[data-test='title'] a",
                                "h3 a"
                            ]
                            for selector in url_selectors:
                                url_elem = resultado.find_element(By.CSS_SELECTOR, selector)
                                if url_elem:
                                    url_art = url_elem.get_attribute("href")
                                    if url_art:
                                        # Extraer DOI de la URL de Springer
                                        doi_match = re.search(r'/article/10\.1007/([^/?]+)', url_art)
                                        if doi_match:
                                            doi = f"10.1007/{doi_match.group(1)}"
                                        elif url_art.startswith("/"):
                                            url_art = f"https://link.springer.com{url_art}"
                                        break
                        except Exception as e:
                            print(f"[Springer] Error extrayendo URL/DOI: {e}")
                        
                        # Extraer revista/fuente
                        revista = "Springer"
                        try:
                            revista_selectors = [
                                ".app-card-open__authors a[data-test='parent']",
                                "a[data-test='parent']",
                                ".app-card-open__authors a[href*='/journal/']"
                            ]
                            for selector in revista_selectors:
                                revista_elem = resultado.find_element(By.CSS_SELECTOR, selector)
                                if revista_elem and revista_elem.text.strip():
                                    revista = revista_elem.text.strip()
                                    break
                        except Exception as e:
                            print(f"[Springer] Error extrayendo revista: {e}")
                        
                        # Extraer tipo de contenido
                        tipo_articulo = "article"
                        try:
                            tipo_elem = resultado.find_element(By.CSS_SELECTOR, ".c-meta__type[data-test='content-type'], [data-test='content-type'] .c-meta__type")
                            if tipo_elem and tipo_elem.text.strip():
                                tipo_texto = tipo_elem.text.strip().lower()
                                if "chapter" in tipo_texto:
                                    tipo_articulo = "incollection"
                                elif "conference" in tipo_texto:
                                    tipo_articulo = "inproceedings"
                        except:
                            pass
                        
                        # Extraer resumen/descripción
                        resumen = "Resumen no disponible"
                        try:
                            resumen_selectors = [
                                ".app-card-open__description[data-test='description'] p",
                                "[data-test='description'] p",
                                ".app-card-open__description p",
                                ".app-card-open__description"
                            ]
                            for selector in resumen_selectors:
                                resumen_elem = resultado.find_element(By.CSS_SELECTOR, selector)
                                if resumen_elem and resumen_elem.text.strip():
                                    resumen = resumen_elem.text.strip()
                                    break
                        except Exception as e:
                            print(f"[Springer] Error extrayendo resumen: {e}")
                        
                        # Validar que tenemos datos mínimos
                        if titulo == "Título no disponible":
                            continue
                        
                        # Crear entrada del artículo
                        articulo = {
                            "Titulo": titulo,
                            "Autores": autores,
                            "Anio": anio,
                            "DOI": doi,
                            "URL": url_art,
                            "Resumen": resumen,
                            "Revista": revista,
                            "Tipo": tipo_articulo
                        }
                        
                        articulos.append(articulo)
                        total_extraidos += 1
                        
                        print(f"[Springer] Artículo {total_extraidos}: {titulo[:60]}...")
                        
                    except Exception as e:
                        print(f"[Springer] Error procesando resultado {idx+1}: {e}")
                        continue
                
                # Intentar ir a la siguiente página
                if total_extraidos < max_resultados:
                    try:
                        # Buscar botón de siguiente página en Springer
                        next_buttons = driver.find_elements(By.CSS_SELECTOR, 
                            "a[aria-label*='next'], a[aria-label*='Next'], .pagination a:last-child, a[rel='next']")
                        
                        siguiente_encontrado = False
                        for button in next_buttons:
                            aria_label = button.get_attribute("aria-label") or ""
                            if ("next" in aria_label.lower() or 
                                "siguiente" in aria_label.lower() or
                                button.get_attribute("rel") == "next"):
                                print(f"[Springer] Navegando a página {pagina_actual + 1}...")
                                driver.execute_script("arguments[0].click();", button)
                                time.sleep(5)
                                siguiente_encontrado = True
                                break
                        
                        if not siguiente_encontrado:
                            print(f"[Springer] No se encontró enlace a siguiente página")
                            break
                        
                        pagina_actual += 1
                        
                    except Exception as e:
                        print(f"[Springer] Error navegando a siguiente página: {e}")
                        break
                else:
                    break
                    
        except Exception as e:
            print(f"[Scraping] Springer: Error general obteniendo resultados: {e}")
    
    print(f"[Scraping] {base}: Extracción completada. Total de artículos extraídos: {len(articulos)}")
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
