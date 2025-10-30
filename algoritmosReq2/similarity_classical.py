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

# Lista de stopwords bilingüe (ligera) para mejorar sensibilidad en Jaccard/Dice
STOPWORDS = {
    # Español comunes
    "el","la","los","las","un","una","unos","unas","de","del","al","y","o","u","que","en","con","por","para","como","es","son","se","su","sus","a","e","no","si","sí","lo","las","les","le","ya","muy","más","menos","entre","sobre","también","pero","sin","hasta","desde","donde","cuando","cual","cuales","porque","qué","cuál","cuáles",
    # Inglés comunes
    "the","a","an","and","or","but","if","in","on","at","for","of","to","from","by","with","as","is","are","was","were","be","been","being","it","its","this","that","these","those","we","you","they","he","she","i","their","our","your","not","no","yes","do","does","did","can","could","should","would","may","might","than","then","there","here","also","more","most","less"
}

def _tokens(texto: str) -> set[str]:
    """Tokeniza palabras simples, elimina stopwords y normaliza.

    Esta versión ligera mejora la probabilidad de solapamiento entre textos
    similares al eliminar ruido frecuente.
    """
    if not texto:
        return set()
    texto = limpiarTexto(texto)
    toks = re.findall(r"[a-záéíóúüñ0-9]+", texto)
    return {t for t in toks if t not in STOPWORDS}

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
    """Jaccard sobre tokens depurados; fallback a tokens crudos si sale 0.

    Cambiamos heurística: si no hay solapamiento tras quitar stopwords,
    intentamos con tokens crudos (solo normalización simple) para aumentar sensibilidad.
    """
    t1 = _tokens(texto1)
    t2 = _tokens(texto2)
    if not t1 or not t2:
        return 0.0
    inter = len(t1 & t2)
    union = len(t1 | t2)
    if union == 0:
        return 0.0
    j = inter / union
    if j > 0:
        return j
    # Fallback: tokens crudos (sin eliminar stopwords)
    raw1 = set(limpiarTexto(texto1).split())
    raw2 = set(limpiarTexto(texto2).split())
    if not raw1 or not raw2:
        return 0.0
    inter = len(raw1 & raw2)
    union = len(raw1 | raw2)
    return inter / union if union else 0.0

# ------------------------------------------------------
#  2. Cosine Similarity (TF-IDF)
# ------------------------------------------------------
def cosine_tfidf_similarity(texto1, texto2):
    """Coseno TF-IDF con mejoras de sensibilidad: ngramas (1,2) y stopwords bilingüe."""
    textos = [texto1 or "", texto2 or ""]
    vectorizer = TfidfVectorizer(stop_words=list(STOPWORDS), ngram_range=(1, 2), lowercase=True)
    tfidf_matrix = vectorizer.fit_transform(textos)
    similitud = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return float(similitud[0][0])

# ------------------------------------------------------
#  3. Sørensen–Dice Coefficient
# ------------------------------------------------------
def dice_similarity(texto1, texto2):
    """Dice sobre tokens depurados; fallback a tokens crudos si sale 0."""
    t1 = _tokens(texto1)
    t2 = _tokens(texto2)
    if not t1 or not t2:
        return 0.0
    inter = len(t1 & t2)
    den = (len(t1) + len(t2))
    d = (2 * inter) / den if den else 0.0
    if d > 0:
        return d
    raw1 = set(limpiarTexto(texto1).split())
    raw2 = set(limpiarTexto(texto2).split())
    if not raw1 or not raw2:
        return 0.0
    inter = len(raw1 & raw2)
    den = (len(raw1) + len(raw2))
    return (2 * inter) / den if den else 0.0

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

# ------------------------------------------------------
#  5. Coeficiente de solapamiento (Overlap Coefficient)
# ------------------------------------------------------
def overlap_coefficient(texto1: str, texto2: str) -> float:
    a = _tokens(texto1)
    b = _tokens(texto2)
    if not a or not b:
        return 0.0
    inter = len(a & b)
    denom = min(len(a), len(b))
    if denom == 0:
        return 0.0
    return inter / denom


# ------------------------------------------------------
#  6. Jaccard ponderado por TF-IDF (Weighted Jaccard)
# ------------------------------------------------------
def weighted_jaccard_tfidf(texto1: str, texto2: str) -> float:
    """Calcula un Jaccard ponderado con pesos TF-IDF (palabras y bigramas).
    Fallback: si el vocabulario queda vacío, reintenta con TF-IDF de caracteres.
    """
    textos = [texto1 or "", texto2 or ""]
    try:
        vec = TfidfVectorizer(stop_words=list(STOPWORDS), ngram_range=(1, 2), lowercase=True)
        X = vec.fit_transform(textos).toarray()
        v1, v2 = X[0], X[1]
        num = np.minimum(v1, v2).sum()
        den = np.maximum(v1, v2).sum()
        if den == 0:
            # Intentar con TF-IDF de caracteres
            raise ValueError("empty denominator")
        return float(num / den)
    except Exception:
        # Fallback: TF-IDF de caracteres con n en [3,2]
        for n in (3, 2):
            try:
                vec_c = TfidfVectorizer(analyzer='char', ngram_range=(n, n), lowercase=True)
                Xc = vec_c.fit_transform(textos).toarray()
                v1, v2 = Xc[0], Xc[1]
                num = np.minimum(v1, v2).sum()
                den = np.maximum(v1, v2).sum()
                if den > 0:
                    return float(num / den)
            except Exception:
                continue
        return 0.0


# ------------------------------------------------------
#  7. Jaro-Winkler (similaridad a nivel de string)
# ------------------------------------------------------
def _jaro_distance(s1: str, s2: str) -> float:
    if s1 == s2:
        return 1.0
    s1 = s1 or ""
    s2 = s2 or ""
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0
    max_dist = max(len1, len2) // 2 - 1
    match = 0
    hash_s1 = [False] * len1
    hash_s2 = [False] * len2
    for i in range(len1):
        start = max(0, i - max_dist)
        end = min(i + max_dist + 1, len2)
        for j in range(start, end):
            if not hash_s2[j] and s1[i] == s2[j]:
                hash_s1[i] = True
                hash_s2[j] = True
                match += 1
                break
    if match == 0:
        return 0.0
    t = 0
    point = 0
    for i in range(len1):
        if hash_s1[i]:
            while not hash_s2[point]:
                point += 1
            if s1[i] != s2[point]:
                t += 1
            point += 1
    t /= 2
    return (match / len1 + match / len2 + (match - t) / match) / 3.0


def jaro_winkler_similarity(texto1: str, texto2: str, p: float = 0.1) -> float:
    """Versión simple de Jaro-Winkler (p típico 0.1)."""
    s1 = (texto1 or "").strip().lower()
    s2 = (texto2 or "").strip().lower()
    jaro = _jaro_distance(s1, s2)
    # prefijo común hasta 4
    l = 0
    for a, b in zip(s1[:4], s2[:4]):
        if a == b:
            l += 1
        else:
            break
    return float(jaro + l * p * (1 - jaro))
