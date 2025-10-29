import os
import sys
import runpy
import traceback
from pathlib import Path


def _print_step(title: str):
	print("\n" + "=" * 80)
	print(title)
	print("=" * 80 + "\n")


def _safe_run(script_path: Path, title: str, cwd: Path | None = None):
	_print_step(f"Ejecutando: {title}")
	if not script_path.exists():
		raise FileNotFoundError(f"No se encontró el script: {script_path}")
	prev_cwd = Path.cwd()
	try:
		if cwd:
			os.chdir(cwd)
		runpy.run_path(str(script_path), run_name="__main__")
	finally:
		os.chdir(prev_cwd)


def _draw_graph_png(graphml_path: Path, png_path: Path, directed: bool = True, max_nodes: int = 120):
	try:
		import networkx as nx
		import matplotlib
		matplotlib.use("Agg", force=True)
		import matplotlib.pyplot as plt

		if not graphml_path.exists():
			print(f"[Imagen] No existe GraphML: {graphml_path}")
			return False

		G = nx.read_graphml(str(graphml_path))
		if directed and not isinstance(G, nx.DiGraph):
			G = nx.DiGraph(G)
		if not directed and not isinstance(G, nx.Graph):
			G = nx.Graph(G)

		n = G.number_of_nodes()
		if n == 0:
			print(f"[Imagen] Grafo vacío: {graphml_path}")
			return False
		if n > max_nodes:
			print(f"[Imagen] Grafo grande (n={n}). Se omite la imagen para evitar tiempos altos: {png_path}")
			return False

		pos = nx.spring_layout(G, seed=42)
		plt.figure(figsize=(10, 8))
		nx.draw_networkx_nodes(G, pos, node_size=80, node_color="#4C78A8", alpha=0.8)
		nx.draw_networkx_edges(G, pos, alpha=0.3, arrows=directed, width=0.8)
		if n <= 40:
			nx.draw_networkx_labels(G, pos, font_size=7)
		plt.axis('off')
		png_path.parent.mkdir(parents=True, exist_ok=True)
		plt.tight_layout()
		plt.savefig(str(png_path), dpi=200)
		plt.close()
		print(f"[Imagen] Generada: {png_path}")
		return True
	except Exception:
		print(f"[Imagen] Error al generar imagen: {png_path}")
		traceback.print_exc()
		return False


def main():
	base_dir = Path(__file__).resolve().parent
	repo_root = base_dir.parent

	# Rutas de scripts
	construir_path = base_dir / "construir_grafo_citaciones.py"
	cooc_path = base_dir / "grafo_coocurrencia.py"
	scc_path = base_dir / "identificar_scc.py"

	# Carpetas de salida conocidas
	salida_grafo_dir = base_dir / "salida_grafo"
	scc_out_dir = base_dir / "scc_out"
	salida_grafo_dir.mkdir(parents=True, exist_ok=True)
	scc_out_dir.mkdir(parents=True, exist_ok=True)

	# 1) Construir grafo de citaciones (produce: grafo.graphml, grafo_edges.csv, grafo_adj.json)
	_safe_run(construir_path, "1) Construir grafo de citaciones")

	# Generar imagen del grafo de citaciones (si es razonable por tamaño)
	citation_graphml = salida_grafo_dir / "grafo.graphml"
	citation_png = salida_grafo_dir / "grafo.png"
	_draw_graph_png(citation_graphml, citation_png, directed=True)

	# 2) Identificar SCC sobre el grafo de citaciones
	_safe_run(scc_path, "2) Identificar componentes fuertemente conexas (SCC)")

	# Generar imágenes de los subgrafos SCC exportados (tomar algunos de scc_out)
	scc_graphmls = sorted(scc_out_dir.glob("scc_*_size_*.graphml"))
	for gm in scc_graphmls[:5]:  # limitar a los primeros 5
		png = gm.with_suffix(".png")
		_draw_graph_png(gm, png, directed=True)

	# 3) Grafo de coocurrencia (independiente, usa productosUnificados)
	# Este script escribe en una ruta relativa "Scripts grafo/salida_grafo", por eso ajustamos cwd al repo root
	_safe_run(cooc_path, "3) Grafo de coocurrencia (términos)", cwd=repo_root)

	# Imagen del grafo de coocurrencia
	cooc_graphml = salida_grafo_dir / "grafo.graphml"
	cooc_png = salida_grafo_dir / "grafo_coocurrencia.png"
	_draw_graph_png(cooc_graphml, cooc_png, directed=False)

	print("\nPipeline de grafos completado. Revisa:")
	print(f" - Citaciones: {salida_grafo_dir}")
	print(f" - SCC: {scc_out_dir}")


if __name__ == "__main__":
	sys.exit(main())

