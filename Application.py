
from selenium_scripts.selenium_setup import configurar_driver
from selenium_scripts.navigation import login_portal_universidad, obtener_enlaces_bases, buscar_en_base, validar_con_google
from scraping.scraping import extraer_articulos, guardar_articulos_bibtex
from similarity.analysis import run_similarity_analysis
import os
# Importar función para guardar HTML
from html_structure.save_html_selenium import save_html
import subprocess
import sys

import unificar

# Configuración y constantes
URL_BIBLIOTECA = "https://library.uniquindio.edu.co/databases"  # Mantener la URL general
NOMBRES_BASES = ["Springer", "ScienceDirect", "IEEE"]
TERMINOS_BUSQUEDA = ["generative artificial intelligence","Computational Thinking", "AI in Education"]
CARPETA_DATA = "data"

def check_and_setup_env():
    # Check if the virtual environment exists
    if not os.path.exists('venv'):
        print("El entorno virtual no está configurado. Creándolo ahora...")
        if os.name == 'nt':  # Windows
            subprocess.run(['config\\setup_env.bat'], shell=True)
        else:  # Linux/MacOS
            subprocess.run(['bash', 'config/setup_env.sh'])

def main():
	import shutil
	import time
	driver, temp_profile_dir = configurar_driver()
	try:
		print("[Portal] Ingresando al portal de la universidad...")
		driver.get(URL_BIBLIOTECA)
		time.sleep(2)
		save_html(driver, "web_portal_universidad", "index.html")
		enlaces_bases = obtener_enlaces_bases(driver, NOMBRES_BASES)
		print("Enlaces obtenidos:", enlaces_bases)
		for base, url_base in enlaces_bases.items():
			for termino in TERMINOS_BUSQUEDA:
				print(f"[{base}] Buscando el término '{termino}'...")
				driver.get(url_base)
				time.sleep(2)
				save_html(driver, f"{base}_html", f"home_{base}.html")

				# Validar credenciales antes de continuar
				validar_con_google(driver)

				# Intentar login solo si aparece el formulario
				try:
					from selenium.webdriver.common.by import By
					from selenium.webdriver.support.ui import WebDriverWait
					from selenium.webdriver.support import expected_conditions as EC
					WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "username")))
					login_portal_universidad(driver)
					time.sleep(2)
					save_html(driver, f"{base}_html", f"login_{base}.html")
				except Exception:
					pass

				buscar_en_base(driver, url_base, base, termino)
				time.sleep(2)
				save_html(driver, f"{base}_html", f"resultados_{base}_{termino.replace(' ', '_')}.html")
				articulos = extraer_articulos(driver, base, max_resultados=1000)
				guardar_articulos_bibtex(articulos, base, termino, CARPETA_DATA)
	finally:
		driver.quit()
		shutil.rmtree(temp_profile_dir, ignore_errors=True)


check_and_setup_env()

if __name__ == "__main__":
	print("=== Iniciando scraping automatizado y guardado en carpeta 'data' ===")
	main()
	print("=== Proceso de scraping finalizado ===")
	unificar.unificar() # unificamos los bib para obtener el archivo que scara los datos necesarios para los paises

if __name__ == "__main__":
    file_path = "data/unified_articles.csv"  # asegúrate de tenerlo listo
    run_similarity_analysis(file_path) 

















