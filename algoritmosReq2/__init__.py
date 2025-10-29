# Package marker for algoritmosReq2
# Expose commonly used functions if desired
from .similarity_classical import (
    levenshtein_similarity,
    jaccard_similarity,
    cosine_tfidf_similarity,
    dice_similarity,
    jaccard_char_ngrams,
    dice_char_ngrams,
    cosine_tfidf_char,
)

try:
    from .similarity_ai import semantic_similarity  # optional if sentence-transformers is installed
except Exception:
    semantic_similarity = None
