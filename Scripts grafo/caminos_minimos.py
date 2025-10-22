#!/usr/bin/env python3
"""
caminos_minimos.py

Calcula caminos mínimos en el grafo de citaciones (GraphML o CSV de aristas).

Opciones de coste (convierte 'weight' en coste usable por algoritmos de caminos):
  - mode = "inv"       -> cost = 1.0 / weight   (peso alto = coste bajo)
  - mode = "1minus"    -> cost = 1.0 - weight   (peso en [0,1] -> coste en [1,0])
  - mode = "unit"      -> cost = 1.0            (camino sin ponderar)

Usos:
  python caminos_minimos.py --graphml ruta/grafo.graphml --cost-mode inv --dijkstra A B
  python caminos_minimos.py --edges ruta/grafo_edges.csv --cost-mode inv --allpairs floyd --outdir salida
  python caminos_minimos.py --graphml ruta/grafo.graphml --cost-mode inv --all-dijkstra --outdir salida

Salida:
 - CSV con distancias y caminos (según la opción).
 - Estadísticas resumidas impresas en pantalla.
"""
import os
import argparse
import csv
import json
import math
from collections import defaultdict

try:
    import networkx as nx
except Exception:
    print("Error: networkx no está instalado. Ejecuta: pip install networkx")
    raise

# ---------- Configuración por defecto (ajusta rutas si quieres) ----------
DEFAULT_GRAPHML = os.path.join(os.path.dirname(__file__), 'salida_grafo', 'grafo.graphml')
DEFAULT_EDGES_CSV = os.path.join(os.path.dirname(__file__), 'salida_grafo', 'grafo_edges.csv')

# ---------- Carga del grafo ----------
def load_graph(graphml_path=None, edges_csv=None, directed=True):
    """
    Carga un grafo. Prioriza graphml si existe, sino lee CSV de aristas.
    CSV expected columns: source,target,weight (weight opcional)
    """
    if graphml_path and os.path.exists(graphml_path):
        G = nx.read_graphml(graphml_path)
        # NetworkX puede cargar GraphML y devolver Graph o DiGraph según archivo.
        if directed and not isinstance(G, nx.DiGraph):
            G = nx.DiGraph(G)
        print(f"Cargado GraphML: {graphml_path}  (nodos={G.number_of_nodes()}, aristas={G.number_of_edges()})")
        return G
    if edges_csv and os.path.exists(edges_csv):
        G = nx.DiGraph() if directed else nx.Graph()
        with open(edges_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                src = row.get('source') or row.get('Source')
                tgt = row.get('target') or row.get('Target')
                w = row.get('weight') or row.get('Weight') or None
                if src is None or tgt is None:
                    continue
                if w is None or w=='':
                    G.add_edge(src, tgt)
                else:
                    try:
                        G.add_edge(src, tgt, weight=float(w))
                    except:
                        G.add_edge(src, tgt, weight=1.0)
        print(f"Cargado CSV de aristas: {edges_csv}  (nodos={G.number_of_nodes()}, aristas={G.number_of_edges()})")
        return G
    raise FileNotFoundError("No se encontró graphml ni CSV con la ruta indicada.")

# ---------- Añadir atributo 'cost' a partir de 'weight' ----------
def add_cost_attribute(G, mode='inv', min_weight_eps=1e-6):
    """
    Añade atributo 'cost' a cada arista en G según mode:
      - 'inv'    : cost = 1.0 / weight  (si weight==0 usamos 1/min_weight_eps)
      - '1minus' : cost = 1.0 - weight  (si weight en [0,1])
      - 'unit'   : cost = 1.0
    Devuelve G modificado.
    """
    for u, v, data in G.edges(data=True):
        w = data.get('weight', None)
        if w is None:
            # Si no hay peso, asumimos 1.0
            w = 1.0
        try:
            w = float(w)
        except:
            w = 1.0
        if mode == 'inv':
            if w <= 0:
                cost = 1.0 / min_weight_eps
            else:
                cost = 1.0 / w
        elif mode == '1minus':
            # asegurar que weight esté en [0,1]
            if w < 0:
                w = 0.0
            if w > 1:
                # normalizar si fuese mayor que 1
                w = 1.0
            cost = 1.0 - w
            # si cost == 0 (peso 1.0) asignar epsilon pequeño para evitar 0
            if cost == 0:
                cost = min_weight_eps
        else:
            cost = 1.0
        data['cost'] = float(cost)
    return G

# ---------- Dijkstra (single-source or single-pair) ----------
def dijkstra_shortest_path(G, source, target=None, weight_attr='cost'):
    """
    Si target es None: devuelve distancias y caminos desde source a todos
    Si target dado: devuelve (distance, path) o (math.inf, []) si no alcanzable
    """
    if source not in G:
        raise KeyError(f"Source {source} no está en el grafo.")
    if target:
        try:
            length = nx.dijkstra_path_length(G, source, target, weight=weight_attr)
            path = nx.dijkstra_path(G, source, target, weight=weight_attr)
            return length, path
        except nx.NetworkXNoPath:
            return math.inf, []
    else:
        lengths, paths = nx.single_source_dijkstra(G, source, weight=weight_attr)
        return lengths, paths

# ---------- All-pairs: Floyd–Warshall (precaución para grafos grandes) ----------
def floyd_warshall_all_pairs(G, weight_attr='cost'):
    """
    Ejecuta Floyd–Warshall y devuelve distancias dict-of-dict y pred (predecesores).
    O(n^3) tiempo — usar sólo si N pequeño (p. ej. < 1000 idealmente mucho menor).
    """
    print("Ejecutando Floyd–Warshall (todo-pares). Esto puede tardar y usar mucha memoria para grafos grandes.")
    # networkx tiene floyd_warshall_predecessor_and_distance
    pred, dist = nx.floyd_warshall_predecessor_and_distance(G, weight=weight_attr)
    return pred, dist

# ---------- All-pairs via Dijkstra repeated (más escalable) ----------
def all_pairs_dijkstra(G, weight_attr='cost', nodes_limit=None):
    """
    Calcula distancias y caminos all-pairs usando Dijkstra desde cada nodo.
    Si nodes_limit dado, limita a los primeros N nodos (por rendimiento).
    Devuelve:
      distances: dict[source][target] = distance
      paths: dict[source][target] = list(nodos)
    """
    nodes = list(G.nodes())
    if nodes_limit:
        nodes = nodes[:nodes_limit]
    distances = {}
    paths = {}
    for i, s in enumerate(nodes, 1):
        print(f"Dijkstra: origen {i}/{len(nodes)} -> {s}")
        lengths, pths = nx.single_source_dijkstra(G, s, weight=weight_attr)
        distances[s] = lengths
        paths[s] = pths
    return distances, paths

# ---------- Utilidades de salida ----------
def save_distances_csv(dist_dict, outpath):
    """
    dist_dict: dict[source][target] = distance
    Guarda CSV con columnas: source,target,distance
    """
    with open(outpath, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['source','target','distance'])
        for src, targets in dist_dict.items():
            for tgt, d in targets.items():
                w.writerow([src, tgt, d])

def save_paths_csv(paths_dict, outpath):
    """
    paths_dict: dict[source][target] = path list
    Guarda CSV con columnas: source,target,path_len,path (path como JSON)
    """
    with open(outpath, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['source','target','path_len','path'])
        for src, targets in paths_dict.items():
            for tgt, p in targets.items():
                w.writerow([src, tgt, len(p), json.dumps(p, ensure_ascii=False)])

# ---------- Estadísticas útiles ----------
def graph_stats_on_distances(distances):
    """
    distances: dict[source][target] = distance
    Calcula promedio (solo parejas alcanzables), diámetro aproximado (max distancia finita).
    """
    all_d = []
    for src, targets in distances.items():
        for tgt, d in targets.items():
            if d != math.inf and src != tgt:
                all_d.append(d)
    if not all_d:
        return {'count':0, 'avg': None, 'max': None}
    return {'count': len(all_d), 'avg': sum(all_d)/len(all_d), 'max': max(all_d)}

# ---------- CLI ----------
def main():
    parser = argparse.ArgumentParser(description="Calcular caminos mínimos en el grafo de citaciones.")
    parser.add_argument('--graphml', type=str, default=DEFAULT_GRAPHML, help="Ruta al grafo .graphml")
    parser.add_argument('--edges', type=str, default=DEFAULT_EDGES_CSV, help="Ruta al CSV de aristas (source,target,weight)")
    parser.add_argument('--cost-mode', type=str, choices=['inv','1minus','unit'], default='inv',
                        help="Cómo convertir weight -> cost (default inv = 1/weight)")
    parser.add_argument('--dijkstra', nargs='*', help="Si se pasan dos nodos S T: calcula Dijkstra S->T; si un solo nodo S: calcula Dijkstra S->todos")
    parser.add_argument('--allpairs', choices=['floyd','dijkstra'], help="Calcular todas las parejas (peligro de coste si grafo grande)")
    parser.add_argument('--all-dijkstra', action='store_true', help="Ejecutar Dijkstra desde todos los nodos (más escalable que floyd)")
    parser.add_argument('--nodes-limit', type=int, help="Limitar número de orígenes en all-pairs (para pruebas)")
    parser.add_argument('--outdir', type=str, default=os.path.join(os.path.dirname(__file__), 'resultado_caminos'), help="Directorio de salida para CSVs")
    args = parser.parse_args()

    G = load_graph(graphml_path=args.graphml or DEFAULT_GRAPHML, edges_csv=args.edges or DEFAULT_EDGES_CSV)
    G = add_cost_attribute(G, mode=args.cost_mode)

    os.makedirs(args.outdir, exist_ok=True)

    # caso: Dijkstra puntual
    if args.dijkstra:
        if len(args.dijkstra) == 2:
            s, t = args.dijkstra
            print(f"Calculando Dijkstra de {s} a {t} (cost mode={args.cost_mode})")
            dist, path = dijkstra_shortest_path(G, s, t, weight_attr='cost')
            if dist == math.inf:
                print(f"No hay camino de {s} a {t}.")
            else:
                print(f"Distancia coste mínima: {dist}")
                print(f"Camino: {path}")
            # guardar
            with open(os.path.join(args.outdir, f"dijkstra_{s}_to_{t}.json"), 'w', encoding='utf-8') as f:
                json.dump({'source':s, 'target':t, 'distance':dist, 'path':path}, f, ensure_ascii=False, indent=2)
            return
        else:
            s = args.dijkstra[0]
            print(f"Calculando Dijkstra desde {s} a todos (cost mode={args.cost_mode})")
            lengths, paths = dijkstra_shortest_path(G, s, None, weight_attr='cost')
            # guardar CSV y JSON
            save_distances_csv({s:lengths}, os.path.join(args.outdir, f"dijkstra_{s}_distances.csv"))
            save_paths_csv({s:paths}, os.path.join(args.outdir, f"dijkstra_{s}_paths.csv"))
            stats = graph_stats_on_distances({s:lengths})
            print("Estadísticas:", stats)
            return

    # caso: all-pairs
    if args.allpairs == 'floyd':
        pred, dist = floyd_warshall_all_pairs(G, weight_attr='cost')
        # dist es dict[src][tgt] = distance
        save_distances_csv(dist, os.path.join(args.outdir, 'floyd_distances.csv'))
        # no guardamos paths completos (pred permite reconstruir)
        stats = graph_stats_on_distances(dist)
        print("Estadísticas all-pairs (floyd):", stats)
        return

    if args.allpairs == 'dijkstra' or args.all_dijkstra:
        print("Ejecutando Dijkstra desde todos los nodos (o hasta nodes_limit)...")
        distances, paths = all_pairs_dijkstra(G, weight_attr='cost', nodes_limit=args.nodes_limit)
        save_distances_csv(distances, os.path.join(args.outdir, 'allpairs_dijkstra_distances.csv'))
        save_paths_csv(paths, os.path.join(args.outdir, 'allpairs_dijkstra_paths.csv'))
        stats = graph_stats_on_distances(distances)
        print("Estadísticas all-pairs (dijkstra):", stats)
        return

    # Automatización: Ejecutar Dijkstra desde todos los nodos si no se especifican argumentos
    print("No se especificaron argumentos, ejecutando Dijkstra desde todos los nodos por defecto.")
    distances, paths = all_pairs_dijkstra(G, weight_attr='cost')
    save_distances_csv(distances, os.path.join(args.outdir, 'allpairs_dijkstra_distances.csv'))
    save_paths_csv(paths, os.path.join(args.outdir, 'allpairs_dijkstra_paths.csv'))
    stats = graph_stats_on_distances(distances)
    print("Estadísticas all-pairs (dijkstra):", stats)

if __name__ == '__main__':
    main()
