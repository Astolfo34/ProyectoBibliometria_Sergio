# Algoritmos para la implementacion de modelos IA

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Cargamos un modelo preentrenado de Sentence-BERT
# Este modelo entiende bien textos en inglés y español
modeloIA = SentenceTransformer("all-MiniLM-L6-v2")

def semantic_similarity(text1, text2):
    """
    Calcula la similitud semántica entre dos textos usando Sentence-BERT.
    Devuelve un valor entre 0 y 1.
    """
    # Convertir los textos en embeddings (vectores)
    embeddings = modeloIA.encode([text1, text2])
    
    # Calcular similitud coseno entre los dos vectores
    similitud = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    
    return float(similitud)
