import os
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ruta_archivo = os.path.join(os.path.dirname(os.path.dirname(__file__)), "productosUnificados", "productosUnificados.txt")

# Validar la existencia del archivo
if not os.path.exists(ruta_archivo):
    raise FileNotFoundError(f"El archivo {ruta_archivo} no existe. Verifica su ubicación.")

# --- Función para extraer abstracts ---
def extraer_abstracts(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        contenido = f.read()
    abstracts_encontrados = re.findall(r'abstract\s*=\s*\{(.*?)\}', contenido, re.DOTALL | re.IGNORECASE)
    return [a.strip() for a in abstracts_encontrados]

# --- Preprocesamiento de texto ---
def preprocesar(texto):
    texto = texto.lower()
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

# --- Cargar y preprocesar abstracts ---
abstracts = extraer_abstracts(ruta_archivo)
abstracts_prep = [preprocesar(a) for a in abstracts if preprocesar(a)]

print("Número total de abstracts válidos:", len(abstracts_prep))

# --- Tomar solo los primeros 50 abstracts para dendrograma ---
max_abstracts = 50
abstracts_vis = abstracts_prep[:max_abstracts]
labels_vis = [f"Abstract {i+1}" for i in range(len(abstracts_vis))]

if len(abstracts_vis) < 2:
    print("No hay suficientes abstracts para clustering jerárquico.")
    exit()

# --- TF-IDF ---
vectorizador = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizador.fit_transform(abstracts_vis)

# --- Similitud coseno ---
sim_matrix = cosine_similarity(tfidf_matrix)

# Crear la carpeta 'data_graficos' si no existe
data_graficos_path = os.path.join(os.path.dirname(__file__), 'data_graficos')
os.makedirs(data_graficos_path, exist_ok=True)

# --- Clustering jerárquico ---
def clustering_jerarquico(sim_matrix, metodo, labels):
    print(f"\nGenerando dendrograma con método: {metodo}")

    # Convertir similitud a distancia
    distancia = 1 - sim_matrix
    distancia = np.clip(distancia, 0, None)

    # Condensar matriz para linkage
    if distancia.shape[0] == 2:
        dist_condensada = np.array([distancia[0,1]])
    else:
        dist_condensada = squareform(distancia, checks=False)

    linked = linkage(dist_condensada, method=metodo)

    # Dendrograma
    plt.figure(figsize=(12,6))
    dendrogram(linked, labels=labels, orientation='top', leaf_rotation=90)
    plt.title(f"Dendrograma - Clustering Jerárquico ({metodo})")
    plt.xlabel("Abstracts")
    plt.ylabel("Distancia")
    plt.tight_layout()

    # Guardar el gráfico en la carpeta 'data_graficos'
    grafico_path = os.path.join(data_graficos_path, f'dendrograma_{metodo}.png')
    plt.savefig(grafico_path)
    print(f"Gráfico guardado en: {grafico_path}")
    plt.close()

# --- Ejecutar los 3 métodos ---
metodos = ['single', 'complete', 'average']
for m in metodos:
    clustering_jerarquico(sim_matrix, m, labels_vis)

# --- Observaciones ---
print("""
Observaciones:
- Revisar visualmente los dendrogramas para determinar cuál método genera 
  agrupamientos más coherentes.
- 'single': tiende a formar cadenas largas (sensible a outliers)
- 'complete': produce clusters más compactos
- 'average': equilibrio entre single y complete
- Para analizar todos los abstracts (1968), es mejor usar clustering sin dendrograma completo,
  o generar dendrograma de muestra usando los primeros abstracts.
""")


