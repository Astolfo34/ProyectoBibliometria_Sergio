# test_similarity_classical.py
from utils.load_data import load_bib_data
from algoritmosReq2.similarity_classical import (
    jaccard_similarity,
    cosine_tfidf_similarity,
    dice_similarity
)
import random

print("📚 Cargando datos...")
df = load_bib_data()

# Filtrar resúmenes válidos
df_valid = df[df["resumen"].str.len() > 30].reset_index(drop=True)
print(f"Artículos con resumen válido: {len(df_valid)}")

# Seleccionar dos abstracts aleatorios
a1, a2 = random.sample(list(df_valid["resumen"]), 2)
print("\nAbstract 1:", a1[:150], "...")
print("\nAbstract 2:", a2[:150], "...")

# Calcular similitudes
print("\n🔹 Jaccard Similarity:", round(jaccard_similarity(a1, a2), 3))
print("🔹 Dice Similarity:", round(dice_similarity(a1, a2), 3))
print("🔹 Cosine TF-IDF Similarity:", round(cosine_tfidf_similarity(a1, a2), 3))
