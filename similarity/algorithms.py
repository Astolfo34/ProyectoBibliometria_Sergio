import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- Normalización ---
def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-z0-9áéíóúüñç\s]', '', text)
    return text.strip()

# --- Levenshtein distance ---
def levenshtein(a: str, b: str) -> int:
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n
    dp = list(range(m + 1))
    for i, ca in enumerate(a, start=1):
        new = [i] + [0]*m
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            new[j] = min(dp[j] + 1, new[j-1] + 1, dp[j-1] + cost)
        dp = new
    return dp[m]

def normalized_levenshtein(a, b):
    d = levenshtein(a, b)
    return 1 - d / max(len(a), len(b)) if max(len(a), len(b)) > 0 else 0

# --- Jaccard y Dice ---
def get_shingles(text, k=3):
    text = normalize_text(text)
    return {text[i:i+k] for i in range(len(text) - k + 1)}

def jaccard(a, b, k=3):
    A, B = get_shingles(a, k), get_shingles(b, k)
    return len(A & B) / len(A | B) if len(A | B) > 0 else 0

def dice(a, b, k=3):
    A, B = get_shingles(a, k), get_shingles(b, k)
    return (2 * len(A & B)) / (len(A) + len(B)) if (len(A)+len(B)) > 0 else 0

# --- TF-IDF Cosine ---
def cosine_tfidf(texts):
    vectorizer = TfidfVectorizer(ngram_range=(1,2), max_features=5000)
    X = vectorizer.fit_transform(texts)
    return cosine_similarity(X)

# --- SBERT embeddings ---
def sbert_cosine(texts, model_name='all-MiniLM-L6-v2'):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    emb = model.encode(texts, show_progress_bar=False)
    return cosine_similarity(emb)
