import os
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram, cophenet
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

# --- Preparar matriz de distancias (1 - similitud) ---
distancia = 1 - sim_matrix
distancia = np.clip(distancia, 0, None)

# Condensar matriz para linkage
if distancia.shape[0] == 2:
    dist_condensada = np.array([distancia[0, 1]])
else:
    dist_condensada = squareform(distancia, checks=False)

# --- Evaluar métodos con Coeficiente Cophenético (CCC) ---
metodos = ['single', 'complete', 'average']
resultados = {}

print("\nEvaluando métodos de enlace (CCC más alto es mejor):")
for metodo in metodos:
    linked = linkage(dist_condensada, method=metodo)
    ccc, _ = cophenet(linked, dist_condensada)
    resultados[metodo] = {"linked": linked, "ccc": float(ccc)}
    print(f"- {metodo}: CCC = {ccc:.3f}")

# Seleccionar mejor método
mejor_metodo = max(resultados, key=lambda k: resultados[k]["ccc"]) if resultados else None
if mejor_metodo:
    print(f"\nMejor método según CCC: {mejor_metodo} (CCC = {resultados[mejor_metodo]['ccc']:.3f})")

# --- Graficar dendrogramas, resaltando el mejor ---
for metodo in metodos:
    info = resultados[metodo]
    plt.figure(figsize=(12, 6))
    dendrogram(info["linked"], labels=labels_vis, orientation='top', leaf_rotation=90)
    titulo = f"Dendrograma - Clustering Jerárquico ({metodo}) | CCC={info['ccc']:.3f}"
    if metodo == mejor_metodo:
        titulo += " [Mejor]"
    plt.title(titulo)
    plt.xlabel("Abstracts")
    plt.ylabel("Distancia")
    plt.tight_layout()

    grafico_path = os.path.join(data_graficos_path, f'dendrograma_{metodo}.png')
    plt.savefig(grafico_path)
    print(f"Gráfico guardado en: {grafico_path}")
    plt.close()

# --- Resumen visual: barras de CCC por método ---
try:
    plt.figure(figsize=(8, 5))
    metodos_orden = sorted(metodos, key=lambda m: resultados[m]["ccc"], reverse=True)
    valores = [resultados[m]["ccc"] for m in metodos_orden]
    colores = ["tab:green" if m == mejor_metodo else "tab:blue" for m in metodos_orden]
    plt.bar(metodos_orden, valores, color=colores)
    plt.ylabel("Coeficiente Cophenético (CCC)")
    plt.title("Comparación de métodos por CCC (más alto es mejor)")
    for i, v in enumerate(valores):
        plt.text(i, v + 0.005, f"{v:.3f}", ha='center', va='bottom', fontsize=9)
    plt.ylim(0, min(1.0, max(valores) + 0.05))
    plt.tight_layout()
    resumen_path = os.path.join(data_graficos_path, 'resumen_ccc_metodos.png')
    plt.savefig(resumen_path)
    print(f"Resumen visual guardado en: {resumen_path}")
    plt.close()
except Exception as e:
    print(f"No se pudo generar el resumen visual de CCC: {e}")

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


