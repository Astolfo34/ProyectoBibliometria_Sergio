from utils.load_data import load_bib_data as load_data
from sentence_transformers import SentenceTransformer, util
import random

# ===============================
# 1️⃣ Cargar datos
# ===============================
print("📚 Cargando datos...")
df = load_data("data")

# Filtrar artículos con resumen
df_valid = df[df["resumen"].str.strip() != ""]
print(f"Artículos con resumen válido: {len(df_valid)}\n")

# ===============================
# 2️⃣ Seleccionar dos resúmenes aleatorios
# ===============================
sample = df_valid.sample(2, random_state=random.randint(1, 9999))
abstracts = sample["resumen"].tolist()

print("Abstract 1:", abstracts[0][:200], "...\n")
print("Abstract 2:", abstracts[1][:200], "...\n")

# ===============================
# 3️⃣ Modelos IA (Sentence-BERT)
# ===============================
print("🔹 Cargando modelos de similitud IA...\n")

# Modelo 1: all-MiniLM-L6-v2
model1 = SentenceTransformer("all-MiniLM-L6-v2")

# Modelo 2: paraphrase-MiniLM-L12-v2
model2 = SentenceTransformer("paraphrase-MiniLM-L12-v2")

# ===============================
# 4️⃣ Codificar y calcular similitudes
# ===============================
embeddings1 = model1.encode(abstracts, convert_to_tensor=True)
embeddings2 = model2.encode(abstracts, convert_to_tensor=True)

sim1 = util.pytorch_cos_sim(embeddings1[0], embeddings1[1]).item()
sim2 = util.pytorch_cos_sim(embeddings2[0], embeddings2[1]).item()

print(f"🔹 Similitud Semántica (SBERT - all-MiniLM-L6-v2): {sim1:.3f}")
print(f"🔹 Similitud Semántica (SBERT - paraphrase-MiniLM-L12-v2): {sim2:.3f}")
