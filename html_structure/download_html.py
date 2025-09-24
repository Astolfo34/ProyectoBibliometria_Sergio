import requests

# URL de la página de la universidad (ajusta la URL según sea necesario)
URL = "https://www.universidad.edu/"

# Realiza la petición HTTP para obtener el HTML
response = requests.get(URL)

if response.status_code == 200:
    with open("html_structure/universidad_homepage.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("HTML guardado exitosamente en html_structure/universidad_homepage.html")
else:
    print(f"Error al obtener la página: {response.status_code}")
