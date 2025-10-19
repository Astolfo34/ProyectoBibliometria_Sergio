import os
import re
from collections import Counter
import matplotlib.pyplot as plt

ruta_archivo = os.path.join(os.path.dirname(os.path.dirname(__file__)), "productosUnificados", "productosUnificados.txt")

# Validar la existencia del archivo
if not os.path.exists(ruta_archivo):
    raise FileNotFoundError(f"El archivo {ruta_archivo} no existe. Verifica su ubicación.")

# --- Palabras/frases asociadas a la categoría ---
palabras_asociadas = [
    "Generative models", "Prompting", "Machine learning", "Multimodality",
    "Fine-tuning", "Training data", "Algorithmic bias", "Explainability",
    "Transparency", "Ethics", "Privacy", "Personalization",
    "Human-AI interaction", "AI literacy", "Co-creation"
]

# --- Stopwords comunes para ignorar ---
stopwords = set([
    'the', 'and', 'of', 'in', 'to', 'a', 'for', 'on', 'with', 'by', 
    'as', 'is', 'at', 'from', 'an', 'its', 'that', 'this', 'are', 'has', 
    'be', 'was', 'were', 'which', 'or', 'but', 'not', 'we', 'can', 'into', 'have'
])

# --- Función para limpiar y tokenizar ---
def tokenizar(texto):
    texto = texto.lower()
    texto = re.sub(r'[^a-z0-9\s\-]', '', texto)
    tokens = texto.split()
    # Excluir stopwords
    tokens = [t for t in tokens if t not in stopwords]
    return tokens

# --- Leer archivo y extraer abstracts ---
abstracts = []
with open(ruta_archivo, "r", encoding="utf-8") as f:
    contenido = f.read()
    abstracts_encontrados = re.findall(r'abstract\s*=\s*\{(.*?)\}', contenido, re.DOTALL | re.IGNORECASE)
    abstracts = [a.strip() for a in abstracts_encontrados]

# --- Contar frecuencia de palabras/frases asociadas ---
frecuencias_asociadas = Counter()
for abstract in abstracts:
    abstract_lower = abstract.lower()
    for frase in palabras_asociadas:
        frase_lower = frase.lower()
        ocurrencias = len(re.findall(r'\b' + re.escape(frase_lower) + r'\b', abstract_lower))
        if ocurrencias > 0:
            frecuencias_asociadas[frase] += ocurrencias

print("Frecuencia de palabras/frases asociadas:")
for palabra, freq in frecuencias_asociadas.items():
    print(f"{palabra}: {freq}")

# --- Generar listado de palabras/frases relevantes (Top 15) ---
contador_global = Counter()

for abstract in abstracts:
    abstract_lower = abstract.lower()
    # Contar frases exactas de la categoría
    for frase in palabras_asociadas:
        frase_lower = frase.lower()
        ocurrencias = len(re.findall(r'\b' + re.escape(frase_lower) + r'\b', abstract_lower))
        if ocurrencias > 0:
            contador_global[frase] += ocurrencias
    # Contar palabras individuales relevantes (no stopwords y con más de 3 caracteres)
    tokens = tokenizar(abstract)
    for t in tokens:
        if len(t) > 3:
            contador_global[t] += 1

top15 = contador_global.most_common(15)

print("\nTop 15 palabras/frases más relevantes en los abstracts:")
for palabra, freq in top15:
    print(f"{palabra}: {freq}")

# --- Evaluar precisión ---
palabras_originales_lower = [w.lower() for w in palabras_asociadas]
nuevas_palabras = [p for p, _ in top15 if p.lower() not in palabras_originales_lower]
precision = 1 - len(nuevas_palabras)/15

print(f"\nPalabras/frases nuevas: {nuevas_palabras}")
print(f"Precisión aproximada de las nuevas palabras/frases: {precision*100:.2f}%")

# --- Gráfico de barras ---
palabras_grafico = [p for p, _ in top15]
frecuencias_grafico = [f for _, f in top15]

plt.figure(figsize=(12,6))
plt.barh(palabras_grafico[::-1], frecuencias_grafico[::-1], color='skyblue')
plt.xlabel("Frecuencia")
plt.title("Top 15 palabras/frases más relevantes en abstracts")
plt.tight_layout()
plt.show()


