import os
import requests
import logging
import time
import json
import csv

# Configuración de logging para depuración
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def consultar_ror_por_afiliacion(afiliacion):
    """
    Consulta la ROR API para obtener la institución y el país asociado a una afiliación.
    :param afiliacion: Cadena de texto con la afiliación (por ejemplo: "University of Pisa, Italy").
    :return: Diccionario con la institución y el país, o "No encontrado" si no hay coincidencia.
    """
    url = "https://api.ror.org/organizations"
    params = {"query": afiliacion}
    try:
        logging.info(f"Consultando ROR API para la afiliación: {afiliacion}")
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            resultados = resp.json().get("items", [])
            if resultados:
                institucion = resultados[0].get("name", "No encontrado")
                pais = resultados[0].get("country", {}).get("country_name", "No encontrado")
                return {"institucion": institucion, "pais": pais}
            else:
                return {"institucion": "No encontrado", "pais": "No encontrado"}
        else:
            logging.error(f"Error en la solicitud a ROR API: {resp.status_code}")
            return {"institucion": "No encontrado", "pais": "No encontrado"}
    except Exception as e:
        logging.error(f"Error al consultar ROR API: {e}")
        return {"institucion": "No encontrado", "pais": "No encontrado"}

def asignar_paises_a_apellidos(afiliaciones):
    """
    Asigna países a apellidos utilizando la ROR API y optimizando consultas.
    :param afiliaciones: Lista de afiliaciones únicas.
    :return: Diccionario con afiliaciones y sus países asociados.
    """
    resultados = {}
    for afiliacion in set(afiliaciones):  # Usar solo afiliaciones únicas
        resultado = consultar_ror_por_afiliacion(afiliacion)
        resultados[afiliacion] = resultado["pais"]
    return resultados

def consultar_openalex_por_doi(doi):
    """
    Consulta OpenAlex para obtener información de afiliaciones y países a partir de un DOI.
    :param doi: DOI del artículo.
    :return: Lista de países asociados a las instituciones o "No encontrado".
    """
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    try:
        logging.info(f"Consultando OpenAlex para el DOI: {doi}")
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            datos = resp.json()
            instituciones = datos.get("authorships", [])
            paises = []
            for institucion in instituciones:
                for afiliacion in institucion.get("institutions", []):
                    pais_codigo = afiliacion.get("country_code", "No encontrado")
                    if pais_codigo != "No encontrado":
                        paises.append(pais_codigo)
            return list(set(paises)) if paises else ["No encontrado"]
        else:
            logging.warning(f"Error {resp.status_code} al consultar OpenAlex para el DOI: {doi}")
            return ["No encontrado"]
    except Exception as e:
        logging.error(f"Error al consultar OpenAlex para el DOI {doi}: {e}")
        return ["No encontrado"]

def inferir_pais_por_apellido_batch(apellidos, clave_api):
    """
    Usa NamSor en modo batch para inferir países a partir de apellidos.
    :param apellidos: Lista de apellidos únicos.
    :param clave_api: Clave de API para autenticar la solicitud.
    :return: Diccionario con apellidos y sus países inferidos.
    """
    url = "https://v2.namsor.com/NamSorAPIv2/api2/json/batchCountry"
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": clave_api
    }
    resultados = {}
    batch_size = 100  # NamSor permite hasta 100 nombres por llamada batch
    for i in range(0, len(apellidos), batch_size):
        batch = apellidos[i:i + batch_size]
        payload = {"personalNames": [{"name": apellido} for apellido in batch]}
        try:
            logging.info(f"Consultando NamSor para batch de apellidos: {batch}")
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
            if resp.status_code == 200:
                datos = resp.json().get("personalNames", [])
                for resultado in datos:
                    apellido = resultado.get("name", "")
                    pais = resultado.get("country", "No encontrado")
                    resultados[apellido] = pais
            else:
                logging.warning(f"Error {resp.status_code} al consultar NamSor para batch: {batch}")
        except Exception as e:
            logging.error(f"Error al consultar NamSor para batch: {e}")
    return resultados

# Cargar surnames.csv como fallback
def cargar_surnames_fallback(ruta_relativa="requerimiento5/data/data_mapasCalor/surnames.csv"):
    """Carga el CSV de apellidos fallback con columnas esperadas: surname,country"""
    fallback = {}
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ruta_relativa)
    try:
        with open(ruta, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                surname = row.get('surname') or row.get('apellido') or row.get('Surname')
                country = row.get('country') or row.get('pais') or row.get('Country')
                if surname and country:
                    fallback[surname.strip().lower()] = country.strip()
        logging.info(f"Fallback surnames cargado: {len(fallback)} entradas desde {ruta_relativa}")
    except FileNotFoundError:
        logging.warning(f"Archivo fallback no encontrado en {ruta}, se continuará sin fallback")
    except Exception as e:
        logging.error(f"Error al cargar fallback surnames: {e}")
    return fallback

# Escribir CSV de DOIs resueltos
def guardar_resultados_csv(resultados, ruta_salida_relativa="requerimiento5/data/resolved_affiliations.csv"):
    """
    Guarda una lista de resultados en CSV con columnas: doi,autor,revista,apellido,pais
    :param resultados: lista de dicts con keys 'doi','autor','revista','apellido','pais'
    """
    salida_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", os.path.dirname(ruta_salida_relativa))
    os.makedirs(salida_dir, exist_ok=True)
    ruta_salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ruta_salida_relativa)
    campos = ['doi','autor','revista','apellido','pais']
    try:
        with open(ruta_salida, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=campos)
            writer.writeheader()
            for row in resultados:
                writer.writerow({k: row.get(k, '') for k in campos})
        logging.info(f"Resultados guardados en {ruta_salida}")
    except Exception as e:
        logging.error(f"Error al guardar resultados CSV: {e}")

# Integrar fallback y guardar en la función de procesamiento principal
def procesar_dois_y_asignar_paises_estrategia(dois, clave_namsor):
    """
    Procesa DOIs para asignar países a autores utilizando OpenAlex y NamSor.
    :param dois: Lista de DOIs.
    :param clave_namsor: Clave de API para NamSor.
    """
    afiliaciones = []
    resultados_autores = []
    apellidos_sin_afiliacion = set()

    fallback = cargar_surnames_fallback("data/surnames.csv")

    # Paso A: Resolver afiliaciones → país vía OpenAlex
    for doi in dois:
        paises_afiliacion = consultar_openalex_por_doi(doi)
        if paises_afiliacion:
            # para cada autor simulado, añadimos una entrada base (buscaremos autores reales con Crossref si es necesario)
            for pais in paises_afiliacion:
                resultados_autores.append({"doi": doi, "autor": "", "revista": "", "apellido": "", "pais": pais})
        else:
            logging.warning(f"No se encontraron países para el DOI: {doi}")

    # Paso B: Inferir país por apellido para autores sin afiliación
    # Recolectar apellidos faltantes
    for autor in resultados_autores:
        apellido = autor.get("apellido", "")
        if not autor.get("pais") or autor.get("pais") == "No encontrado":
            apellidos_sin_afiliacion.add(apellido)

    # Usar NamSor para inferir los apellidos faltantes
    if apellidos_sin_afiliacion:
        paises_inferidos = inferir_pais_por_apellido_batch([a for a in apellidos_sin_afiliacion if a], clave_namsor)
    else:
        paises_inferidos = {}

    # Asignar países inferidos y fallback
    resultados_finales = []
    for autor in resultados_autores:
        apellido = autor.get('apellido','').strip()
        pais = autor.get('pais')
        if not pais or pais == 'No encontrado':
            # primero intentar NamSor
            if apellido and apellido in paises_inferidos:
                pais = paises_inferidos.get(apellido)
            else:
                # fallback local
                pais = fallback.get(apellido.lower(), 'No encontrado')
        resultados_finales.append({
            'doi': autor.get('doi',''),
            'autor': autor.get('autor',''),
            'revista': autor.get('revista',''),
            'apellido': apellido,
            'pais': pais
        })

    # Guardar resultados resueltos en CSV (solo los que tengan pais distinto de 'No encontrado')
    res_para_guardar = [r for r in resultados_finales if r['pais'] and r['pais'] != 'No encontrado']
    guardar_resultados_csv(res_para_guardar)

    # Mostrar un resumen
    logging.info(f"Total DOIs procesados: {len(dois)}")
    logging.info(f"Registros resueltos guardados: {len(res_para_guardar)}")

def procesar_dois_y_asignar_paises(dois):
    """
    Procesa una lista de DOIs, extrae afiliaciones, asigna países a apellidos y muestra resultados.
    :param dois: Lista de DOIs.
    """
    afiliaciones = []
    resultados_autores = []

    for doi in dois:
        url = f"https://api.crossref.org/works/{doi}"
        headers = {"User-Agent": "Python-Scraper/1.0 (mailto:example@email.com)"}
        intentos = 3  # Número máximo de reintentos
        while intentos > 0:
            try:
                respuesta = requests.get(url, headers=headers, timeout=10)  # Incrementar timeout a 10 segundos
                if respuesta.status_code != 200:
                    logging.warning(f"Error {respuesta.status_code} al consultar DOI: {doi}")
                    break

                datos = respuesta.json().get("message", {})
                for autor in datos.get("author", []):
                    nombre = f"{autor.get('given', '')} {autor.get('family', '')}".strip()
                    apellido = autor.get('family', '').strip()
                    afiliaciones_autor = autor.get('affiliation', [])
                    if afiliaciones_autor and isinstance(afiliaciones_autor, list):
                        afiliacion = afiliaciones_autor[0].get('name', '')
                    else:
                        afiliacion = ''

                    if afiliacion:
                        afiliaciones.append(afiliacion)

                    resultados_autores.append({
                        "nombre": nombre,
                        "apellido": apellido,
                        "afiliacion": afiliacion
                    })
                break  # Salir del bucle si la solicitud fue exitosa
            except requests.exceptions.ReadTimeout:
                intentos -= 1
                logging.warning(f"Timeout al consultar DOI {doi}. Reintentando... ({3 - intentos}/3)")
            except Exception as e:
                logging.error(f"Error al consultar DOI {doi}: {e}")
                break

    # Asignar países a las afiliaciones únicas
    paises_por_afiliacion = asignar_paises_a_apellidos(afiliaciones)

    # Mostrar resultados con países asignados
    for autor in resultados_autores:
        afiliacion = autor["afiliacion"]
        pais = paises_por_afiliacion.get(afiliacion, "No encontrado")
        print(f"Autor: {autor['nombre']}, Apellido: {autor['apellido']}, País: {pais}")

def extrar_dois_de_articulos(ruta_archivos):
    """
    Extrae DOIs de una lista de archivos de artículos .bib, considerando todos los autores.
    :param ruta_archivos: Ruta donde se encuentran los archivos .bib.
    :return: Lista de DOIs extraídos.
    """
    dois = []
    for archivo in os.listdir(ruta_archivos):
        if archivo.endswith(".bib"):
            with open(os.path.join(ruta_archivos, archivo), 'r', encoding='utf-8') as f:
                contenido = f.read()
                lineas = contenido.splitlines()
                for linea in lineas:
                    if "doi" in linea.lower():
                        partes = linea.split("=")
                        if len(partes) > 1:
                            doi = partes[1].strip().strip('{},"')
                            dois.append(doi)
    return dois

ruta_archivos = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../data")
clave_namsor ="46a5d99548ef99ee84c109b3e11eda6c"
dois = extrar_dois_de_articulos(ruta_archivos)
procesar_dois_y_asignar_paises_estrategia(dois,clave_namsor)
# Ejemplo de uso:
# dois = extrar_dois_de_articulos(["articulo1.txt", "articulo2.txt"])
# procesar_dois_y_asignar_paises(dois, clave_namsor)
