import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def save_html(driver, folder_name, file_name):
    """
    Guarda el HTML actual del driver en una subcarpeta de html_structure.
    """
    base_dir = os.path.join(os.path.dirname(__file__), folder_name)
    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"[HTML] Guardado en {file_path}")

## Este archivo ahora solo contiene la función utilitaria. No ejecuta nada por sí solo.
