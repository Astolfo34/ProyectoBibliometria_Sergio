from algoritmosReq2.similarity_classical import levenshtein_similarity
from utils.load_data import load_bib_data

df = load_bib_data()

# Filtra los artículos que tienen resumen real
df_valid = df[df["resumen"].str.len() > 30].reset_index(drop=True)

print(f"Artículos con resumen válido: {len(df_valid)}")

# Para seleccionar 2 al azar
text1 = df_valid.iloc[0]["resumen"]
text2 = df_valid.iloc[1]["resumen"]

print("\nAbstract 1:", text1[:200], "...\n")
print("Abstract 2:", text2[:200], "...\n")

similarity = levenshtein_similarity(text1, text2)
print(f"🔹 Similitud Levenshtein entre los dos textos: {similarity}")

print("Cantidad total de artículos:", len(df))
print("Primeros 5 resúmenes reales:")
for i, row in df_valid.head(5).iterrows():
    print(f"Título: {row['titulo']}")
    print(f"Archivo: {row['archivo']}")
    print(f"Resumen: {row['resumen'][:250]}...\n")
