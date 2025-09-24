"""
Módulo selenium_setup.py
------------------------
Configuración del driver de Selenium para automatización de navegador.
Autor: [Tu Nombre]
Fecha: 2025-09-23
Descripción: Este módulo configura y retorna el driver de Selenium para Chrome, compatible con Linux y Windows.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import tempfile
import shutil

def configurar_driver():
    """
    Configura el driver de Chrome para Selenium usando un perfil temporal único.
    :return: (driver, temp_profile_dir) - Instancia de webdriver.Chrome y ruta del perfil temporal
    """
    opciones = Options()
    opciones.add_argument("--disable-gpu")
    opciones.add_argument("--no-sandbox")
    # Crear un directorio temporal para el perfil de usuario
    temp_profile_dir = tempfile.mkdtemp(prefix="selenium_profile_")
    opciones.add_argument(f"--user-data-dir={temp_profile_dir}")
    driver = webdriver.Chrome(options=opciones)
    return driver, temp_profile_dir
