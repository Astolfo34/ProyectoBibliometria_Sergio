#!/usr/bin/env python3
"""
Script de prueba para validar el scraping mejorado
"""

from selenium_scripts.selenium_setup import configurar_driver
from selenium_scripts.navigation import obtener_enlaces_bases, buscar_en_base, validar_con_google
from scraping.scraping import extraer_articulos, guardar_articulos_bibtex
import time

def test_scraping():
    """
    Función de prueba para validar el scraping mejorado
    """
    URL_BIBLIOTECA = "https://library.uniquindio.edu.co/databases"
    NOMBRES_BASES = ["Springer"]  # Probar solo con una base primero
    TERMINO_PRUEBA = "artificial intelligence"  # Término con muchos resultados
    
    driver, temp_profile_dir = configurar_driver()
    
    try:
        print("[TEST] Iniciando prueba de scraping mejorado...")
        
        # Navegar al portal
        driver.get(URL_BIBLIOTECA)
        time.sleep(2)
        
        # Obtener enlaces de bases de datos
        enlaces_bases = obtener_enlaces_bases(driver, NOMBRES_BASES)
        print(f"[TEST] Enlaces obtenidos: {enlaces_bases}")
        
        # Probar con Springer
        for base, url_base in enlaces_bases.items():
            print(f"[TEST] Probando {base} con término '{TERMINO_PRUEBA}'...")
            
            driver.get(url_base)
            time.sleep(2)
            
            # Validar credenciales
            validar_con_google(driver)
            
            # Buscar término
            buscar_en_base(driver, url_base, base, TERMINO_PRUEBA)
            time.sleep(3)
            
            # Extraer solo los primeros 10 artículos para prueba
            print(f"[TEST] Extrayendo artículos de {base}...")
            articulos = extraer_articulos(driver, base, max_resultados=10)
            
            # Guardar resultados
            if articulos:
                guardar_articulos_bibtex(articulos, base, TERMINO_PRUEBA, "test_data")
                print(f"[TEST] ✅ {base}: {len(articulos)} artículos extraídos correctamente")
                
                # Mostrar ejemplo de los primeros 3 artículos
                for i, articulo in enumerate(articulos[:3], 1):
                    print(f"[TEST] Artículo {i}:")
                    print(f"  Título: {articulo['Titulo'][:80]}...")
                    print(f"  Autores: {articulo['Autores'][:60]}...")
                    print(f"  Año: {articulo['Anio']}")
                    print(f"  DOI: {articulo['DOI']}")
                    print(f"  Revista: {articulo['Revista']}")
                    print("")
            else:
                print(f"[TEST] ❌ {base}: No se extrajeron artículos")
    
    except Exception as e:
        print(f"[TEST] Error durante la prueba: {e}")
    
    finally:
        driver.quit()
        import shutil
        shutil.rmtree(temp_profile_dir, ignore_errors=True)

if __name__ == "__main__":
    # Crear directorio de prueba
    import os
    os.makedirs("test_data", exist_ok=True)
    
    test_scraping()