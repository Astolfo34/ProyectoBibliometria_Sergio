import os
import re
import itertools
from collections import Counter
import networkx as nx
import pandas as pd

# Rutas
ruta_archivo = os.path.join(os.path.dirname(os.path.dirname(__file__)), "productosUnificados", "productosUnificados.txt")
salida_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "salida_grafo")
os.makedirs(salida_dir, exist_ok=True)


# Leer abstracts
with open(ruta_archivo, "r", encoding="utf-8") as f:
    contenido = f.read()
    abstracts = re.findall(r'abstract\s*=\s*\{(.*?)\}', contenido, re.DOTALL | re.IGNORECASE)
    abstracts = [a.strip().lower() for a in abstracts if a.strip()]

# Palabras o frases frecuentes 
top_terminos = [
    "machine learning", "generative models", "prompting", "ethics", "training data",
    "fine-tuning", "multimodality", "transparency", "privacy", "explainability",
    "human-ai interaction", "ai literacy", "co-creation", "personalization", "algorithmic bias"
]

# Construir grafo de coocurrencia
G = nx.Graph()
G.add_nodes_from(top_terminos)

for abstract in abstracts:
    presentes = [term for term in top_terminos if re.search(r'\b' + re.escape(term) + r'\b', abstract)]
    # Crear aristas entre términos que coocurren en el mismo abstract
    for a, b in itertools.combinations(presentes, 2):
        if G.has_edge(a, b):
            G[a][b]['weight'] += 1
        else:
            G.add_edge(a, b, weight=1)

# Calcular grado de cada nodo
nodo_data = []
for nodo in G.nodes():
    nodo_data.append({
        "term": nodo,
        "degree": G.degree(nodo),
        "weighted_degree": G.degree(nodo, weight="weight")
    })

df_nodes = pd.DataFrame(nodo_data).sort_values(by="degree", ascending=False)
df_nodes.to_csv(os.path.join(salida_dir, "grafo_nodes.csv"), index=False)


# Guardar aristas
edges = [{"source": u, "target": v, "weight": d["weight"]} for u, v, d in G.edges(data=True)]
pd.DataFrame(edges).to_csv(os.path.join(salida_dir, "grafo_edges.csv"), index=False)

# Detectar componentes conexos
components = list(nx.connected_components(G))
df_components = pd.DataFrame({
    "component_id": range(1, len(components) + 1),
    "terms": [", ".join(sorted(list(c))) for c in components]
})
df_components.to_csv(os.path.join(salida_dir, "grafo_componentes.csv"), index=False)

# Guardar grafo en formato GraphML 
nx.write_graphml(G, os.path.join(salida_dir, "grafo.graphml"))

print("✅ Grafo generado con exito.")
print(f"📁 Archivos guardados en: {salida_dir}")
