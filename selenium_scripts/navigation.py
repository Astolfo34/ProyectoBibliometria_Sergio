"""
Funciones para navegación y búsqueda en portales académicos.
Descripción: Este módulo contiene funciones para navegar y buscar en portales de bases de datos académicas.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv
from html_structure.save_html_selenium import save_html
from bs4 import BeautifulSoup

def login_portal_universidad(driver):
    """
    Automatiza el login en el portal de la universidad usando credenciales del archivo .env
    """
    load_dotenv()
    usuario = os.getenv("EMAIL")
    contrasena = os.getenv("PASSWORD")
    # Ajusta los selectores según el portal real
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(usuario)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "password"))).send_keys(contrasena)
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, "loginButton"))).click()
    time.sleep(3)

"""
def ir_a_facultad_ingenieria(driver):
    # Esta función ya no es necesaria, la navegación a Fac. Ingeniería se realiza en obtener_enlaces_bases.
    pass
"""

def obtener_enlaces_bases(driver, nombres_bases):
    """
    Obtiene los enlaces de las bases de datos listadas en nombres_bases.
    """
    """
    Busca y retorna los enlaces de las bases de datos seleccionadas.
    """
    enlaces = {}
    try:
        # Esperar y expandir el details de Fac. Ingeniería si está colapsado
        details_xpath = "//details[.//h2[contains(text(), 'Fac. Ingeniería')]]"
        details_elem = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, details_xpath))
        )
        # Si el details está colapsado, expandirlo
        if details_elem.get_attribute("open") is None:
            driver.execute_script("arguments[0].scrollIntoView();", details_elem)
            summary = details_elem.find_element(By.TAG_NAME, "summary")
            summary.click()
            time.sleep(1)
        # Buscar todos los artículos dentro de Fac. Ingeniería
        articulos = details_elem.find_elements(By.TAG_NAME, "article")
        for nombre_base in nombres_bases:
            encontrado = False
            for articulo in articulos:
                try:
                    # Buscar el título de la base
                    titulo_elem = articulo.find_element(By.CSS_SELECTOR, ".result-title")
                    if nombre_base.lower() in titulo_elem.text.lower():
                        enlace_elem = titulo_elem.find_element(By.TAG_NAME, "a")
                        enlace_url = enlace_elem.get_attribute("href")
                        enlaces[nombre_base] = enlace_url
                        encontrado = True
                        break
                except Exception:
                    continue
            if not encontrado:
                print(f"No se encontró el enlace para {nombre_base} en Fac. Ingeniería.")
    except Exception as error:
        print(f"Error navegando Fac. Ingeniería: {error}")
    return enlaces

def buscar_en_base(driver, url_base, base, termino):
    """
    Realiza la búsqueda del término en la base de datos seleccionada.
    """
    if base == "IEEE":
        url_busqueda = url_base + "?queryText=" + termino.replace(" ", "+")
    elif base == "ScienceDirect":
        url_busqueda = url_base + "?qs=" + termino.replace(" ", "+")
    elif base == "Springer":
        driver.get(url_base)
        try:
            # Buscar el campo de entrada y el botón de búsqueda
            caja_busqueda = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.app-homepage-hero__input"))
            )
            caja_busqueda.clear()
            caja_busqueda.send_keys(termino)
            boton_busqueda = driver.find_element(By.CSS_SELECTOR, "button.app-homepage-hero__button")
            boton_busqueda.click()
        except Exception as e:
            print(f"[Springer] Error en la búsqueda: {e}")
        return
    else:
        url_busqueda = url_base
    driver.get(url_busqueda)
    try:
        caja_busqueda = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search']"))
        )
        caja_busqueda.clear()
        caja_busqueda.send_keys(termino)
        caja_busqueda.send_keys(Keys.ENTER)
    except Exception:
        pass
    # Scroll para cargar más resultados
    altura = driver.execute_script("return document.body.scrollHeight")
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(4)
        nueva_altura = driver.execute_script("return document.body.scrollHeight")
        if nueva_altura == altura:
            break
        altura = nueva_altura

def validar_con_google(driver):
    """
    Automatiza el proceso de validación en la web de IntelProxy usando Google y captura el HTML de la página.
    """
    try:
        # Capturar el HTML de la página de IntelProxy antes de interactuar
        html_content = driver.page_source
        save_html(driver, "web_portal_universidad", "intelproxy.html")

        # Buscar y hacer clic en el botón de Google
        boton_google = driver.find_element(By.ID, "btn-google")
        boton_google.click()

        # Capturar el HTML de la ventana de Google (correo electrónico)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "identifierId"))
        )
        save_html(driver, "web_portal_universidad", "google_login_email.html")

        # Ingresar credenciales de Google
        load_dotenv()
        usuario = os.getenv("EMAIL")
        contrasena = os.getenv("PASSWORD")

        # Llenar el campo de correo electrónico
        driver.find_element(By.ID, "identifierId").send_keys(usuario)
        driver.find_element(By.ID, "identifierNext").click()

        # Capturar el HTML de la ventana de Google (contraseña)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "Passwd"))
        )
        save_html(driver, "web_portal_universidad", "google_login_password.html")

        # Llenar el campo de contraseña
        password_field = driver.find_element(By.NAME, "Passwd")
        password_field.clear()
        password_field.send_keys(contrasena)
        driver.find_element(By.ID, "passwordNext").click()

        print("[Validación] Inicio de sesión con Google completado.")
    except Exception as e:
        print(f"[Error] Falló la validación con Google: {e}")
