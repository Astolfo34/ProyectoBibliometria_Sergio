import pandas as pd
from similarity.algorithms import (
    normalize_text, normalized_levenshtein, jaccard, dice,
    cosine_tfidf, sbert_cosine
)

def run_similarity_analysis(file_path):
    df = pd.read_csv(file_path)
    df['abstract'] = df['abstract'].fillna('').apply(normalize_text)

    texts = df['abstract'].tolist()

    print("Calculando TF-IDF cosine...")
    M_tfidf = cosine_tfidf(texts)

    print("Calculando SBERT cosine...")
    M_sbert = sbert_cosine(texts)

    results = []
    for i in range(len(df)):
        for j in range(i+1, len(df)):
            lev = normalized_levenshtein(texts[i], texts[j])
            jac = jaccard(texts[i], texts[j])
            dic = dice(texts[i], texts[j])
            tfidf_val = M_tfidf[i, j]
            sbert_val = M_sbert[i, j]
            results.append({
                "id_a": df.loc[i, 'id'] if 'id' in df else i,
                "id_b": df.loc[j, 'id'] if 'id' in df else j,
                "levenshtein": lev,
                "jaccard": jac,
                "dice": dic,
                "tfidf_cosine": tfidf_val,
                "sbert_cosine": sbert_val
            })
    out_df = pd.DataFrame(results)
    out_df.to_csv("outputs/similarity_results.csv", index=False)
    print("✅ Resultados guardados en outputs/similarity_results.csv")
