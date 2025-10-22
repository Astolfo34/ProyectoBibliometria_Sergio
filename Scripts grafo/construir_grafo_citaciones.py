#!/usr/bin/env python3
"""
construir_grafo_citaciones.py

Lee un archivo con entradas BibTeX/estilo similar (varias entradas @article{...})
y construye un grafo dirigido de citaciones. Las aristas se determinan mediante:
 - Detección explícita si existe un campo 'references' (opcional)
 - Inferencia por similitud de títulos y solapamiento de autores (TF-IDF + coseno)

Salida:
 - GraphML (grafo completo) -> <salida_graphml>
 - CSV con aristas -> <salida_edges_csv>
 - JSON con lista de adyacencia -> <salida_adj_json>

Ejecución:
    python construir_grafo_citaciones.py --input productosUnificados.txt --outdir ./salida
"""
import os
import re
import json
import csv
import argparse
from collections import defaultdict

# librerías necesarias para la versión optimizada
try:
    import networkx as nx
except Exception:
    nx = None

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel
except Exception:
    np = None
    TfidfVectorizer = None
    linear_kernel = None

try:
    from tqdm import tqdm
except Exception:
    tqdm = None

# --- Utilidades ---
def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    s = re.sub(r'\s+', ' ', s)
    return s.lower()

def author_list_from_field(field: str):
    if not field:
        return []
    if ' and ' in field.lower():
        parts = [p.strip() for p in re.split(r'\s+[aA][nN][dD]\s+', field)]
    else:
        parts = [p.strip() for p in field.split(',') if p.strip()]
    cleaned = []
    for p in parts:
        p = re.sub(r'[{}"]', '', p).strip()
        if not p:
            continue
        cleaned.append(p)
    return cleaned

def author_overlap(a_list, b_list):
    if not a_list or not b_list:
        return 0.0
    a_last = {normalize_text(x).split()[-1] for x in a_list if x}
    b_last = {normalize_text(x).split()[-1] for x in b_list if x}
    inter = a_last.intersection(b_last)
    denom = min(len(a_last), len(b_last)) if min(len(a_last), len(b_last))>0 else 1
    return len(inter)/denom

# --- Parser simple de BibTeX-like ---
def parse_unified_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    entries = re.split(r'\n(?=@\w+\{)', content)
    parsed = []
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        header_match = re.match(r'@(\w+)\s*\{\s*([^,]+),', entry, re.IGNORECASE)
        bibtype = header_match.group(1) if header_match else "unknown"
        bibkey = header_match.group(2) if header_match else f"entry_{len(parsed)+1}"

        fields = {}
        for m in re.finditer(r'(\w+)\s*=\s*(\{([^}]*)\}|"([^"]*)"|([^,\n]+))\s*,?', entry, re.IGNORECASE):
            field = m.group(1).strip().lower()
            val = m.group(3) or m.group(4) or m.group(5) or ""
            fields[field] = val.strip()

        title = fields.get('title', '')
        author = fields.get('author', '') or fields.get('authors', '')
        year = fields.get('year', '')
        doi = fields.get('doi', '')
        url = fields.get('url', '')
        abstract = fields.get('abstract', '')
        references = fields.get('references', '')
        parsed.append({
            'bibkey': bibkey,
            'type': bibtype,
            'title': title,
            'authors_raw': author,
            'authors': author_list_from_field(author),
            'year': year,
            'doi': doi,
            'url': url,
            'abstract': abstract,
            'references_raw': references,
            'raw_entry': entry
        })
    return parsed

# --- Construcción del grafo (optimizada con TF-IDF) ---
def build_citation_graph_optimized(entries, title_weight=0.7, author_weight=0.3,
                                   title_threshold=0.50, sim_threshold=0.60, use_progress=True):
    """
    - Vectoriza títulos con TF-IDF
    - Calcula similitud coseno y considera sólo pares con similitud >= title_threshold
    - Combina similitud de título y solapamiento de autores para score final
    - Añade arista A -> B si score >= sim_threshold
    """
    if TfidfVectorizer is None or linear_kernel is None or np is None:
        raise RuntimeError("scikit-learn / numpy no instalados. Ejecuta: pip install scikit-learn numpy")

    if nx:
        G = nx.DiGraph()
    else:
        G = {'nodes': {}, 'edges': defaultdict(dict)}

    for e in entries:
        node_id = e['bibkey']
        if nx:
            G.add_node(node_id, title=e['title'], authors=e['authors'], year=e['year'],
                       doi=e['doi'], url=e['url'])
        else:
            G['nodes'][node_id] = {'title': e['title'], 'authors': e['authors'], 'year': e['year'],
                                   'doi': e['doi'], 'url': e['url']}

    n = len(entries)
    titles = [e['title'] or "" for e in entries]

    vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1,2), min_df=1)
    tfidf = vectorizer.fit_transform(titles)

    cos_sim = linear_kernel(tfidf, tfidf)  # (n x n) dense array

    author_lastnames = []
    for e in entries:
        lastnames = {normalize_text(a).split()[-1] for a in e['authors'] if normalize_text(a)}
        author_lastnames.append(lastnames)

    # referencias explícitas map
    doi_map = {}
    for e in entries:
        if e['doi']:
            doi_map[normalize_text(e['doi']).replace('doi:', '').strip()] = e['bibkey']
        if e['url']:
            doi_map[normalize_text(e['url']).strip()] = e['bibkey']

    rng = range(n)
    iterator = tqdm(rng, desc="Construyendo aristas", unit="origen") if (use_progress and tqdm) else rng

    for i in iterator:
        a = entries[i]
        sims_row = cos_sim[i]
        candidate_js = np.where(sims_row >= title_threshold)[0]
        for j in candidate_js:
            if i == j:
                continue
            b = entries[j]
            explicit = False
            if a.get('references_raw'):
                if b['bibkey'] in a['references_raw']:
                    explicit = True
                else:
                    for doi_k, bk in doi_map.items():
                        if doi_k in a['references_raw'] and bk == b['bibkey']:
                            explicit = True
            if not explicit and b.get('doi'):
                if normalize_text(b['doi']) in normalize_text(a['raw_entry']):
                    explicit = True

            if explicit:
                score = 1.0
            else:
                title_sim = float(sims_row[j])
                Aset = author_lastnames[i]
                Bset = author_lastnames[j]
                if len(Aset) == 0 or len(Bset) == 0:
                    author_ov = 0.0
                else:
                    author_ov = len(Aset.intersection(Bset)) / max(1, min(len(Aset), len(Bset)))
                score = title_weight * title_sim + author_weight * author_ov

            if score >= sim_threshold:
                if nx:
                    G.add_edge(a['bibkey'], b['bibkey'], weight=round(float(score), 4))
                else:
                    G['edges'][a['bibkey']][b['bibkey']] = round(float(score), 4)

    return G

# --- Guardar salidas (sanitiza atributos para GraphML) ---
def export_graph(G, outdir, prefix='grafo'):
    os.makedirs(outdir, exist_ok=True)
    graphml_path = os.path.join(outdir, f"{prefix}.graphml")
    edges_csv_path = os.path.join(outdir, f"{prefix}_edges.csv")
    adj_json_path = os.path.join(outdir, f"{prefix}_adj.json")

    if nx:
        # Crear una copia "saneada" del grafo transformando listas/dicts a strings
        G_sane = nx.DiGraph()
        for n, data in G.nodes(data=True):
            sane_data = {}
            for k, v in data.items():
                if isinstance(v, (list, tuple, set)):
                    sane_data[k] = "; ".join(map(str, v))
                elif isinstance(v, dict):
                    sane_data[k] = json.dumps(v, ensure_ascii=False)
                else:
                    sane_data[k] = v
            G_sane.add_node(n, **sane_data)

        for u, v, data in G.edges(data=True):
            sane_edge = {}
            for k, val in data.items():
                if isinstance(val, (list, tuple, set, dict)):
                    sane_edge[k] = json.dumps(val, ensure_ascii=False)
                else:
                    sane_edge[k] = val
            G_sane.add_edge(u, v, **sane_edge)

        # Intentar escribir GraphML (si falta lxml, networkx usará su writer por defecto)
        try:
            nx.write_graphml(G_sane, graphml_path)
        except Exception as e:
            print("Advertencia al escribir GraphML:", e)
            # intentar de nuevo (al menos generará CSV/JSON aunque GraphML falle)
            try:
                nx.write_graphml(G_sane, graphml_path)
            except Exception as e2:
                print("No se pudo escribir GraphML:", e2)

        # edges csv
        with open(edges_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['source', 'target', 'weight'])
            for u, v, data in G_sane.edges(data=True):
                writer.writerow([u, v, data.get('weight', 1.0)])

        # adjacency json
        adj = defaultdict(dict)
        for u, v, data in G_sane.edges(data=True):
            adj[u][v] = data.get('weight', 1.0)
        with open(adj_json_path, 'w', encoding='utf-8') as f:
            json.dump(adj, f, indent=2, ensure_ascii=False)

    else:
        # sin networkx: comportamiento previo
        nodes_path = os.path.join(outdir, f"{prefix}_nodes.json")
        with open(nodes_path, 'w', encoding='utf-8') as f:
            json.dump(G['nodes'], f, indent=2, ensure_ascii=False)
        with open(edges_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['source', 'target', 'weight'])
            for u, targets in G['edges'].items():
                for v, w in targets.items():
                    writer.writerow([u, v, w])
        with open(adj_json_path, 'w', encoding='utf-8') as f:
            json.dump(G['edges'], f, indent=2, ensure_ascii=False)

    return graphml_path, edges_csv_path, adj_json_path

# --- Main CLI ---
def main():
    parser = argparse.ArgumentParser(description="Construir grafo de citaciones a partir de archivo unificado BibTeX-like.")
    parser.add_argument('--input', '-i', required=False, default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "productosUnificados", "productos_unificados.txt"), help="Archivo de entrada (productosUnificados/productos_unificados.txt por defecto)")
    parser.add_argument('--outdir', '-o', required=False, default='salida_grafo', help="Directorio de salida")
    parser.add_argument('--threshold', '-t', type=float, default=0.60, help="Umbral final de similitud para inferir citación (0-1)")
    parser.add_argument('--title-threshold', type=float, default=0.50, help="Umbral mínimo de similitud de título para generar candidatos (0-1)")
    parser.add_argument('--no-progress', action='store_true', help="Desactivar barra de progreso")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print("ERROR: archivo de entrada no encontrado:", args.input)
        return

    print("Parseando entradas...")
    entries = parse_unified_file(args.input)
    print(f"Entradas detectadas: {len(entries)}")

    print("Construyendo grafo (inferencias por título y autores)...")
    G = build_citation_graph_optimized(entries,
                                      title_weight=0.7,
                                      author_weight=0.3,
                                      title_threshold=args.title_threshold,
                                      sim_threshold=args.threshold,
                                      use_progress=not args.no_progress)

    print("Exportando grafo...")
    graphml_path, edges_csv_path, adj_json_path = export_graph(G, args.outdir)
    print("Archivos generados:")
    if nx:
        print(" - GraphML:", graphml_path)
    else:
        print(" - Nodes JSON (sin networkx):", os.path.join(args.outdir, "grafo_nodes.json"))
    print(" - Edges CSV:", edges_csv_path)
    print(" - Adjacency JSON:", adj_json_path)

    if nx:
        print("Resumen: nodos =", G.number_of_nodes(), "aristas =", G.number_of_edges())
    else:
        print("Resumen: nodos =", len(G['nodes']), "aristas =", sum(len(v) for v in G['edges'].values()))

if __name__ == '__main__':
    main()

