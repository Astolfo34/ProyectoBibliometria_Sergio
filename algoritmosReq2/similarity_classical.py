# Algoritmos implementados para 
import re
import numpy as np
import Levenshtein
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ------------------------------------------------------
#  Función auxiliar: limpiar texto
# ------------------------------------------------------
def limpiarTexto(texto):
    texto = texto.lower()
    texto = re.sub(r'[^a-záéíóúüñ0-9\s]', '', texto)
    return texto.strip()

# ------------------------------------------------------
#  1. levenshtein
# ------------------------------------------------------
def levenshtein_similarity(texto1, texto2):
    """
    Calcula la similitud entre dos textos usando la distancia de Levenshtein.
    Retorna un valor entre 0 y 1 (donde 1 = textos idénticos).
    """
    if not texto1 or not texto2:
        return 0.0
    
    distancia = Levenshtein.distance(texto1, texto2)
    max_len = max(len(texto1), len(texto2))
    
    if max_len == 0:
        return 1.0
    
    # Convertimos la distancia en una similitud
    similarity = 1 - (distancia / max_len)
    return round(similarity, 3)

# ------------------------------------------------------
#  2. Jaccard Similarity
# ------------------------------------------------------
def jaccard_similarity(texto1, texto2):
    t1 = set(limpiarTexto(texto1).split())
    t2 = set(limpiarTexto(texto2).split())
    if not t1 or not t2:
        return 0.0
    return len(t1.intersection(t2)) / len(t1.union(t2))

# ------------------------------------------------------
#  2. Cosine Similarity (TF-IDF)
# ------------------------------------------------------
def cosine_tfidf_similarity(texto1, texto2):
    textos = [texto1, texto2]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(textos)
    similitud = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return similitud[0][0]

# ------------------------------------------------------
#  3. Sørensen–Dice Coefficient
# ------------------------------------------------------
def dice_similarity(texto1, texto2):
    t1 = set(limpiarTexto(texto1).split())
    t2 = set(limpiarTexto(texto2).split())
    if not t1 or not t2:
        return 0.0
    return 2 * len(t1.intersection(t2)) / (len(t1) + len(t2))

# ------------------------------------------------------
#  4. Jaccard y Dice con n-gramas de CARACTERES
# ------------------------------------------------------
def _char_ngrams(s: str, n: int) -> set[str]:
    if not s:
        return set()
    n = max(1, int(n or 1))
    s = s.strip().lower()
    if len(s) < n:
        return {s}
    return {s[i:i+n] for i in range(len(s) - n + 1)}


def jaccard_char_ngrams(texto1: str, texto2: str, n: int = 3) -> float:
    a = _char_ngrams(texto1, n)
    b = _char_ngrams(texto2, n)
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    if union == 0:
        return 0.0
    return inter / union


def dice_char_ngrams(texto1: str, texto2: str, n: int = 3) -> float:
    a = _char_ngrams(texto1, n)
    b = _char_ngrams(texto2, n)
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return (2 * inter) / (len(a) + len(b))


def cosine_tfidf_char(texto1: str, texto2: str, n: int = 3) -> float:
    """
    Coseno de TF-IDF con n-gramas de caracteres.
    n: tamaño del n-grama de caracteres (por ejemplo, 2, 3 o 4).
    """
    textos = [texto1 or "", texto2 or ""]
    n = max(1, int(n or 1))
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(n, n), lowercase=True)
    tfidf = vectorizer.fit_transform(textos)
    sim = cosine_similarity(tfidf[0:1], tfidf[1:2])
    return float(sim[0][0])
