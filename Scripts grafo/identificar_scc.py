#!/usr/bin/env python3
"""
identificar_scc.py

Identifica componentes fuertemente conexas (SCC) en un grafo dirigido de citaciones.
- Carga GraphML (preferido) o CSV de aristas.
- Calcula SCC (strongly connected components).
- Guarda:
  - scc_list.csv : lista de (component_id, node, component_size)
  - scc_summary.csv : lista de (component_id, size)
  - scc_<id>.graphml : subgrafo exportado para las N mayores componentes (opcional)
  - scc_summary.json : resumen en JSON

Ejecución ejemplo:
  python identificar_scc.py --graphml "ruta/grafo.graphml" --outdir "salida_scc" --export-top 10
"""
import os
import argparse
import csv
import json
from collections import defaultdict

try:
    import networkx as nx
except Exception:
    raise SystemExit("networkx no instalado. Ejecuta: pip install networkx")

def load_graph(graphml_path=None, edges_csv=None):
    if graphml_path and os.path.exists(graphml_path):
        G = nx.read_graphml(graphml_path)
        # asegurarse DiGraph
        if not isinstance(G, nx.DiGraph):
            G = nx.DiGraph(G)
        print(f"Cargado GraphML: {graphml_path} (nodos={G.number_of_nodes()}, aristas={G.number_of_edges()})")
        return G
    if edges_csv and os.path.exists(edges_csv):
        G = nx.DiGraph()
        with open(edges_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                s = row.get('source') or row.get('Source')
                t = row.get('target') or row.get('Target')
                w = row.get('weight') or row.get('Weight')
                if s is None or t is None:
                    continue
                if w:
                    try:
                        G.add_edge(s, t, weight=float(w))
                    except:
                        G.add_edge(s, t)
                else:
                    G.add_edge(s, t)
        print(f"Cargado CSV de aristas: {edges_csv} (nodos={G.number_of_nodes()}, aristas={G.number_of_edges()})")
        return G
    raise FileNotFoundError("No se encontró archivo GraphML ni CSV de aristas en las rutas dadas.")

def identify_scc(G):
    # networkx.strongly_connected_components devuelve componentes como iterador de sets
    scc_iter = nx.strongly_connected_components(G)
    components = []
    for comp in scc_iter:
        components.append(set(comp))
    # ordenar por tamaño descendente
    components.sort(key=lambda s: len(s), reverse=True)
    return components

def export_results(components, G, outdir, export_top=0):
    os.makedirs(outdir, exist_ok=True)
    # scc_summary.csv: component_id,size
    summary_path = os.path.join(outdir, "scc_summary.csv")
    with open(summary_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['component_id','size'])
        for idx, comp in enumerate(components, 1):
            writer.writerow([idx, len(comp)])
    # scc_list.csv: component_id,node,component_size
    list_path = os.path.join(outdir, "scc_list.csv")
    with open(list_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['component_id','node','component_size'])
        for idx, comp in enumerate(components, 1):
            size = len(comp)
            for n in comp:
                writer.writerow([idx, n, size])
    # resumen JSON
    summary = {
        'total_components': len(components),
        'components_sorted_sizes': [len(c) for c in components]
    }
    with open(os.path.join(outdir, "scc_summary.json"), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # exportar subgrafos para las N primeras components si se pide
    exported = []
    if export_top and export_top > 0:
        for idx, comp in enumerate(components[:export_top], 1):
            sub = G.subgraph(comp).copy()
            path = os.path.join(outdir, f"scc_{idx}_size_{len(comp)}.graphml")
            try:
                nx.write_graphml(sub, path)
                exported.append(path)
            except Exception as e:
                print(f"Advertencia: no se pudo escribir GraphML para scc_{idx}: {e}")
    return summary_path, list_path, exported

def print_report(components, top_k=10):
    print("Total de componentes fuertemente conexas (SCC):", len(components))
    sizes = [len(c) for c in components]
    if sizes:
        print("Tamaño mayor:", max(sizes), "Tamaño medio:", sum(sizes)/len(sizes))
    print(f"Top {min(top_k, len(components))} componentes (id:size):")
    for idx, comp in enumerate(components[:top_k], 1):
        print(f"  {idx}: {len(comp)}")

def main():
    parser = argparse.ArgumentParser(description="Identificar componentes fuertemente conexas (SCC) en el grafo.")
    parser.add_argument('--graphml', type=str, default=os.path.join(os.path.dirname(__file__), 'salida_grafo', 'grafo.graphml'), help="Ruta al archivo .graphml")
    parser.add_argument('--edges', type=str, default=os.path.join(os.path.dirname(__file__), 'salida_grafo', 'grafo_edges.csv'), help="Ruta al CSV de aristas (source,target,weight)")
    parser.add_argument('--outdir', type=str, default=os.path.join(os.path.dirname(__file__), 'scc_out'), help="Directorio de salida")
    parser.add_argument('--export-top', type=int, default=10, help="Exportar subgrafo GraphML de las N mayores SCC (por defecto 10)")
    parser.add_argument('--top-report', type=int, default=20, help="Cuántas SCC mostrar en el reporte")
    args = parser.parse_args()

    G = load_graph(graphml_path=args.graphml, edges_csv=args.edges)
    components = identify_scc(G)
    print_report(components, top_k=args.top_report)
    spath, lpath, exported = export_results(components, G, args.outdir, export_top=args.export_top)
    print("Archivos generados:")
    print(" - summary CSV:", spath)
    print(" - node list CSV:", lpath)
    if exported:
        for p in exported:
            print(" - exported subgraph:", p)

if __name__ == '__main__':
    main()
