from __future__ import annotations

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple
import csv

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


logger = logging.getLogger("informePDF")


def find_latest_image(folder: Path, pattern: str = "*.png") -> Optional[Path]:
	if not folder.exists():
		return None
	imgs = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
	return imgs[0] if imgs else None


def find_latest_file(folder: Path, pattern: str) -> Optional[Path]:
	"""Devuelve el archivo más reciente que cumple el patrón o None."""
	if not folder.exists():
		return None
	files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
	return files[0] if files else None


def add_cover_page(pdf: PdfPages, title: str, subtitle: str, bullets: List[str]) -> None:
	plt.figure(figsize=(11.69, 8.27))  # A4 landscape approx in inches
	plt.axis('off')
	plt.text(0.5, 0.8, title, ha='center', va='center', fontsize=24, weight='bold')
	plt.text(0.5, 0.72, subtitle, ha='center', va='center', fontsize=12)
	y = 0.6
	for b in bullets:
		plt.text(0.1, y, f"• {b}", fontsize=12)
		y -= 0.06
	plt.text(0.5, 0.08, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ha='center', fontsize=10, alpha=0.7)
	pdf.savefig(bbox_inches='tight')
	plt.close()


def add_image_page(pdf: PdfPages, image_path: Path, title: str, caption: str = "") -> None:
	plt.figure(figsize=(11.69, 8.27))
	plt.suptitle(title, fontsize=16, weight='bold')
	plt.subplot(1, 1, 1)
	plt.imshow(plt.imread(str(image_path)))
	plt.axis('off')
	if caption:
		plt.figtext(0.5, 0.02, caption, wrap=True, ha='center', fontsize=10)
	pdf.savefig(bbox_inches='tight')
	plt.close()


def add_texts_side_by_side(pdf: PdfPages, title: str, left_title: str, left_text: str, right_title: str, right_text: str) -> None:
	"""Agrega una página con dos columnas de texto (izquierda/derecha) con envoltura conservadora."""
	import textwrap

	fig = plt.figure(figsize=(11.69, 8.27))
	fig.suptitle(title, fontsize=16, weight='bold')
	# Área sin ejes
	ax = plt.subplot(1, 1, 1)
	ax.axis('off')

	# Márgenes y anchos de columna (landscape)
	left_x = 0.06
	right_x = 0.53
	col_width = 46  # caracteres aprox. por columna
	y_start = 0.88
	line_h = 0.035

	# Título columna izquierda
	fig.text(left_x, y_start, left_title, ha='left', va='top', fontsize=12, weight='bold')
	y = y_start - 0.05
	for ln in textwrap.fill(left_text or "(vacío)", width=col_width).splitlines():
		fig.text(left_x, y, ln, ha='left', va='top', fontsize=10)
		y -= line_h

	# Título columna derecha
	fig.text(right_x, y_start, right_title, ha='left', va='top', fontsize=12, weight='bold')
	y2 = y_start - 0.05
	for ln in textwrap.fill(right_text or "(vacío)", width=col_width).splitlines():
		fig.text(right_x, y2, ln, ha='left', va='top', fontsize=10)
		y2 -= line_h

	pdf.savefig(bbox_inches='tight')
	plt.close()


def add_table_pages_from_csv(pdf: PdfPages, csv_path: Path, title: str, max_rows_per_page: int = 25) -> None:
	if not csv_path.exists():
		add_cover_page(pdf, f"Tabla no disponible: {title}", f"No se encontró {csv_path}", bullets=["Ejecuta el generador correspondiente para producir el CSV."])
		return
	rows: List[List[str]] = []
	with open(csv_path, 'r', encoding='utf-8') as f:
		reader = csv.reader(f)
		try:
			headers = next(reader)
		except StopIteration:
			headers = []
		for r in reader:
			rows.append(r)

	if not rows:
		add_cover_page(pdf, f"Tabla vacía: {title}", f"El archivo {csv_path.name} no contiene filas.", bullets=[])
		return

	total_pages = (len(rows) + max_rows_per_page - 1) // max_rows_per_page
	for page_idx in range(total_pages):
		start = page_idx * max_rows_per_page
		end = min(len(rows), start + max_rows_per_page)
		chunk = rows[start:end]
		plt.figure(figsize=(11.69, 8.27))
		plt.suptitle(f"{title} (página {page_idx+1}/{total_pages})", fontsize=14, weight='bold')
		ax = plt.subplot(1, 1, 1)
		ax.axis('off')
		table = ax.table(cellText=chunk, colLabels=headers, loc='center', cellLoc='left')
		table.auto_set_font_size(False)
		table.set_fontsize(8)
		table.scale(1, 1.3)
		plt.figtext(0.5, 0.02, str(csv_path), ha='center', fontsize=8, alpha=0.6)
		pdf.savefig(bbox_inches='tight')
		plt.close()


# === Utilidades de métricas de grafos (opcionales) ===
def _metrics_from_adj_json(adj_path: Path) -> Optional[dict]:
	"""Lee un adj.json (dict de dict) y calcula métricas simples de grafo dirigido."""
	try:
		if not adj_path.exists():
			return None
		with open(adj_path, 'r', encoding='utf-8') as f:
			adj = json.load(f)
		nodes = set(adj.keys())
		edges = 0
		out_deg = {}
		in_deg = {}
		for u, nbrs in adj.items():
			k = len(nbrs)
			edges += k
			out_deg[u] = k
			for v in nbrs.keys():
				nodes.add(v)
				in_deg[v] = in_deg.get(v, 0) + 1
				out_deg.setdefault(v, 0)
		n = len(nodes)
		m = edges
		# Top-5 por out-degree
		top5_out = sorted(out_deg.items(), key=lambda x: x[1], reverse=True)[:5]
		# Top-5 por in-degree
		top5_in = sorted(in_deg.items(), key=lambda x: x[1], reverse=True)[:5]
		density = None
		try:
			if n > 1:
				density = m / (n * (n - 1))
		except Exception:
			pass
		return {
			'n': n,
			'm': m,
			'density': density,
			'top5_out': top5_out,
			'top5_in': top5_in,
		}
	except Exception:
		return None


def _metrics_from_graphml(graphml_path: Path, undirected: bool = True) -> Optional[dict]:
	"""Lee un GraphML y calcula métricas básicas; si undirected=True lo trata como no dirigido."""
	try:
		import networkx as nx  # opcional
		if not graphml_path.exists():
			return None
		G = nx.read_graphml(str(graphml_path))
		if undirected and not isinstance(G, nx.Graph):
			G = nx.Graph(G)
		if not undirected and not isinstance(G, nx.DiGraph):
			G = nx.DiGraph(G)
		n = G.number_of_nodes()
		m = G.number_of_edges()
		density = None
		try:
			density = nx.density(G)
		except Exception:
			pass
		# Top-5 por grado
		degs = G.degree()
		top5 = sorted(degs, key=lambda x: x[1], reverse=True)[:5]
		return {
			'n': n,
			'm': m,
			'density': density,
			'top5_degree': [(str(n), int(d)) for n, d in top5],
		}
	except Exception:
		return None


def main() -> int:
	logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s', datefmt='%H:%M:%S')

	project_root = Path(__file__).resolve().parents[2]

	# Rutas de entrada
	heatmap_img = project_root / 'requerimiento5' / 'data' / 'heatmap_affiliations.png'
	# Fallback: muchas ejecuciones guardan el heatmap en data/data_mapasCalor/
	heatmap_img_alt = project_root / 'requerimiento5' / 'data' / 'data_mapasCalor' / 'heatmap_affiliations.png'
	nube_dir = project_root / 'requerimiento5' / 'data' / 'data_nubePalabras'
	linea_dir = project_root / 'requerimiento5' / 'data' / 'data_lineaTemporal'
	csv_year = linea_dir / 'conteo_por_anio.csv'
	csv_year_j = linea_dir / 'conteo_por_anio_revista.csv'

	# Detectar últimas imágenes disponibles
	nube_img = find_latest_image(nube_dir)
	linea_img = find_latest_image(linea_dir)
	heatmap_found = None
	if heatmap_img.exists():
		heatmap_found = heatmap_img
	elif heatmap_img_alt.exists():
		heatmap_found = heatmap_img_alt

	logger.info(f"Heatmap: {'OK' if heatmap_found else 'NO ENCONTRADO'}")
	logger.info(f"Nube de palabras: {nube_img if nube_img else 'NO ENCONTRADA'}")
	logger.info(f"Línea temporal: {linea_img if linea_img else 'NO ENCONTRADA'}")

	# Salida
	out_dir = project_root / 'requerimiento5' / 'data' / 'data_informes'
	out_dir.mkdir(parents=True, exist_ok=True)
	out_pdf = out_dir / f"informe_bibliometria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

	# Crear PDF
	with PdfPages(str(out_pdf)) as pdf:
		add_cover_page(
			pdf,
			title="Informe Bibliométrico - Resultados",
			subtitle="Representaciones: mapa de calor (afiliaciones por país), nube de palabras (términos relevantes) y línea temporal (publicaciones)",
			bullets=[
				"Objetivo: brindar una visión sintética de tendencias, distribución geográfica y vocabulario dominante.",
				"Fuente: documentos unificados provenientes de bases indexadas (archivos productosUnificados).",
				"Notas: este informe refleja los artefactos generados en esta ejecución (últimas imágenes disponibles).",
			],
		)

		if heatmap_found:
			add_image_page(
				pdf,
				heatmap_found,
				title="Mapa de calor por país de afiliación",
				caption="Intensidad proporcional al número de afiliaciones detectadas por país. Fuente: resolved_affiliations.csv",
			)
		else:
			add_cover_page(
				pdf,
				title="Mapa de calor no disponible",
				subtitle="No se encontró la imagen 'heatmap_affiliations.png' en requerimiento5/data/",
				bullets=["Ejecuta generarMapaCalor.py para producirla si corresponde."],
			)

		if nube_img:
			add_image_page(
				pdf,
				nube_img,
				title="Nube de palabras de términos relevantes",
				caption="Generada a partir de los abstracts extraídos. Stopwords ES/EN y heurísticas de limpieza aplicadas.",
			)
		else:
			add_cover_page(
				pdf,
				title="Nube de palabras no disponible",
				subtitle="No se encontró ninguna imagen en requerimiento5/data/data_nubePalabras/",
				bullets=["Ejecuta nubePalabras.py para generarla."],
			)

		if linea_img:
			add_image_page(
				pdf,
				linea_img,
				title="Serie temporal de publicaciones por año",
				caption="Panel izquierdo: total anual. Panel derecho: desagregado por las revistas/venues más frecuentes.",
			)
		else:
			add_cover_page(
				pdf,
				title="Línea temporal no disponible",
				subtitle="No se encontró ninguna imagen en requerimiento5/data/data_lineaTemporal/",
				bullets=["Ejecuta generar_lineaTemporal.py para generarla."],
			)

		# Añadir tablas CSV
		add_table_pages_from_csv(pdf, csv_year, title="Conteo de publicaciones por año")
		add_table_pages_from_csv(pdf, csv_year_j, title="Conteo de publicaciones por año y revista")

		# === Sección opcional: Resultados de grafos ===
		try:
			grafos_dir = project_root / 'Scripts grafo'
			salida_grafo = grafos_dir / 'salida_grafo'
			scc_out = grafos_dir / 'scc_out'

			# Imágenes principales (si existen)
			citations_img = salida_grafo / 'grafo.png'
			cooc_img = salida_grafo / 'grafo_coocurrencia.png'

			if citations_img.exists():
				add_image_page(
					pdf,
					citations_img,
					title="Grafo de citaciones (dirigido)",
					caption="Grafo dirigido generado a partir del archivo unificado. Layout fuerza de resortes; la densidad y los hubs pueden sugerir áreas con alta interconexión de citas.",
				)

			if cooc_img.exists():
				add_image_page(
					pdf,
					cooc_img,
					title="Grafo de coocurrencia de términos",
					caption="Relaciones entre términos frecuentes que aparecen en el mismo abstract. Los enlaces reflejan coocurrencias y la agrupación sugiere tópicos cercanos.",
				)

			# Imágenes de SCC (tomar algunas)
			if scc_out.exists():
				scc_imgs = sorted(
					[s for s in scc_out.glob('scc_*_size_*.png') if s.is_file()],
					key=lambda p: (
						-int(re.search(r"_size_(\d+)\.png$", p.name).group(1)) if re.search(r"_size_(\d+)\.png$", p.name) else 0,
						-p.stat().st_mtime
					),
				)
				for img in scc_imgs[:3]:  # incluir las 3 mayores si existen
					size_match = re.search(r"_size_(\d+)\.png$", img.name)
					size_txt = size_match.group(1) if size_match else "?"
					add_image_page(
						pdf,
						img,
						title=f"Subgrafo SCC (tamaño {size_txt})",
						caption="Una SCC (componente fuertemente conexa) indica un grupo de artículos con citación mutuamente alcanzable; tamaños mayores pueden señalar clústeres temáticos consolidados.",
					)

			# Tablas de SCC (opcional)
			scc_summary_csv = scc_out / 'scc_summary.csv'
			if scc_summary_csv.exists():
				add_table_pages_from_csv(pdf, scc_summary_csv, title="Resumen de tamaños de SCC")

			# Conclusiones (opcional, a partir de scc_summary.json si existe)
			scc_summary_json = scc_out / 'scc_summary.json'
			bullets: List[str] = []
			if scc_summary_json.exists():
				try:
					with open(scc_summary_json, 'r', encoding='utf-8') as f:
						info = json.load(f)
						total = info.get('total_components')
						sizes = info.get('components_sorted_sizes') or []
						mayor = max(sizes) if sizes else None
						if total is not None:
							bullets.append(f"Se detectaron {total} componentes fuertemente conexas (SCC).")
						if mayor is not None:
							bullets.append(f"La SCC más grande tiene tamaño {mayor}, lo que sugiere un clúster central de citaciones.")
						if sizes:
							bullets.append("La distribución de tamaños decae rápidamente: muchas SCC pequeñas y pocas grandes (estructura típica en grafos de citación).")
				except Exception:
					pass

			# Métricas cuantitativas (opcionales) de grafos
			# 1) Citaciones: derivar desde adj.json si está presente (no lo sobreescribe coocurrencia)
			cit_adj = salida_grafo / 'grafo_adj.json'
			cit_metrics = _metrics_from_adj_json(cit_adj)
			if cit_metrics:
				bullets.append(
					f"Citaciones: nodos={cit_metrics['n']}, aristas={cit_metrics['m']}, "
					+ (f"densidad={cit_metrics['density']:.4f}" if cit_metrics['density'] is not None else "densidad=N/A")
				)
				if cit_metrics['top5_in']:
					names = ", ".join([f"{n}({d})" for n, d in cit_metrics['top5_in']])
					bullets.append(f"Top-5 por in-degree (citados): {names}")
				if cit_metrics['top5_out']:
					names = ", ".join([f"{n}({d})" for n, d in cit_metrics['top5_out']])
					bullets.append(f"Top-5 por out-degree (citantes): {names}")

			# 2) Coocurrencia: leer el GraphML actual (tras orquestador suele corresponder a coocurrencia)
			cooc_metrics = _metrics_from_graphml(salida_grafo / 'grafo.graphml', undirected=True)
			if cooc_metrics:
				bullets.append(
					f"Coocurrencia: nodos={cooc_metrics['n']}, aristas={cooc_metrics['m']}, "
					+ (f"densidad={cooc_metrics['density']:.4f}" if cooc_metrics['density'] is not None else "densidad=N/A")
				)
				if cooc_metrics['top5_degree']:
					names = ", ".join([f"{n}({d})" for n, d in cooc_metrics['top5_degree']])
					bullets.append(f"Top-5 términos por grado: {names}")

			if citations_img.exists():
				bullets.append("El grafo de citaciones revela nodos con alta conectividad que podrían ser trabajos seminales o de revisión.")
			if cooc_img.exists():
				bullets.append("El grafo de coocurrencia sugiere agrupaciones de términos que apuntan a subtemas recurrentes.")

			if bullets:
				add_cover_page(
					pdf,
					title="Conclusiones sobre grafos (síntesis)",
					subtitle="Resumen interpretativo a partir de los artefactos de grafos disponibles",
					bullets=bullets,
				)
		except Exception as e:
			logger.warning(f"Sección de grafos omitida por error no crítico: {e}")

		# === Sección: Comparación de textos y similitud (Req2) ===
		try:
			req2_dir = project_root / 'algoritmosReq2' / 'data_req2'
			latest_csv = find_latest_file(req2_dir, 'similarity_results_*.csv') if req2_dir.exists() else None
			latest_plot = find_latest_image(req2_dir, 'similarity_plot_*.png') if req2_dir.exists() else None

			if not (latest_csv or latest_plot):
				add_cover_page(
					pdf,
					title="Resultados de similitud (Req2) no disponibles",
					subtitle="No se encontraron artefactos en algoritmosReq2/data_req2/",
					bullets=[
						"Ejecuta algoritmosReq2/mainReq2.py para generar CSV e imagen.",
					],
				)
			else:
				# Leer textos y resultados del CSV más reciente
				texts: Tuple[str, str] | None = None
				best_algo: Optional[str] = None
				best_score: Optional[float] = None
				result_map: dict = {}
				if latest_csv and latest_csv.exists():
					try:
						import csv as _csv
						with open(latest_csv, 'r', encoding='utf-8') as f:
							reader = _csv.DictReader(f)
							row = next(reader, None)
							if row:
								text1 = row.get('text1', '')
								text2 = row.get('text2', '')
								texts = (text1, text2)
								# Extraer puntajes numéricos
								keys_interes = [
									'levenshtein', 'jaccard', 'cosine_tfidf', 'dice', 'overlap_coeff',
									'weighted_jaccard_tfidf', 'jaro_winkler', 'jaccard_char', 'dice_char', 'semantic_sbert'
								]
								for k in keys_interes:
									v = row.get(k)
									try:
										fv = float(v) if v not in (None, '', 'None') else None
										result_map[k] = fv
										if fv is not None and (best_score is None or fv > best_score):
											best_score, best_algo = fv, k
									except Exception:
										result_map[k] = None
					except Exception:
						texts = None

				# Página con textos comparados
				if texts:
					add_texts_side_by_side(
						pdf,
						title="Comparación de textos (Req2)",
						left_title="Texto 1",
						left_text=texts[0],
						right_title="Texto 2",
						right_text=texts[1],
					)
				else:
					add_cover_page(
						pdf,
						title="Textos comparados no disponibles",
						subtitle="No fue posible leer text1/text2 del CSV de resultados.",
						bullets=[str(latest_csv) if latest_csv else "(sin CSV)"]
					)

				# Imagen de resultados por algoritmo
				if latest_plot and latest_plot.exists():
					add_image_page(
						pdf,
						latest_plot,
						title="Similitud por algoritmo (Req2)",
						caption=f"Fuente: {latest_csv.name if latest_csv else ''}",
					)
				
				# Conclusiones genéricas según mejor algoritmo
				if best_algo is not None and best_score is not None:
					conclu_map = {
						'levenshtein': [
							"El mayor puntaje se obtuvo con Levenshtein (ediciones).",
							"Sugiere que los textos difieren principalmente por pequeñas variaciones (ortografía, orden o palabras puntuales).",
						],
						'jaccard': [
							"Predomina el solapamiento de vocabulario (Jaccard por palabra).",
							"Los textos comparten un conjunto relevante de términos, aunque no necesariamente en el mismo contexto.",
						],
						'cosine_tfidf': [
							"Alta similitud en términos discriminativos (Cosine TF-IDF).",
							"Indica coincidencia en conceptos clave más allá de palabras comunes.",
						],
						'dice': [
							"Fuerte solapamiento léxico (Dice por palabra).",
							"Las coincidencias de vocabulario son consistentes entre ambos textos.",
						],
						'overlap_coeff': [
							"Coeficiente de solapamiento elevado.",
							"Uno de los textos parece contener gran parte del vocabulario del otro.",
						],
						'weighted_jaccard_tfidf': [
							"Solapamiento ponderado por relevancia (TF-IDF) destacado.",
							"Los términos compartidos son además importantes dentro de cada texto.",
						],
						'jaro_winkler': [
							"Alta similitud de cadenas (Jaro–Winkler).",
							"Adecuado para títulos o fragmentos cortos con variaciones menores.",
						],
						'jaccard_char': [
							"Gran coincidencia en n-gramas de caracteres (Jaccard).",
							"Sugiere cercanía morfológica, incluso si cambia la segmentación en palabras.",
						],
						'dice_char': [
							"Coincidencia alta de n-gramas de caracteres (Dice).",
							"Indicativo de títulos o frases muy parecidas a nivel de caracteres.",
						],
						'semantic_sbert': [
							"La similitud semántica (SBERT) es la más alta.",
							"Los textos tratan temas muy cercanos incluso con vocabulario distinto.",
						],
					}
					bul = [
						f"Mejor algoritmo: {best_algo} con score ≈ {best_score:.3f}",
					] + conclu_map.get(best_algo, ["El algoritmo con mayor puntaje sugiere una alta cercanía entre ambos textos."])
					add_cover_page(
						pdf,
						title="Conclusiones (Req2)",
						subtitle="Síntesis genérica basada en el algoritmo con mayor similitud",
						bullets=bul,
					)
		except Exception as e:
			logger.warning(f"Sección Req2 omitida por error no crítico: {e}")

		# Página final con conclusiones genéricas
		add_cover_page(
			pdf,
			title="Conclusiones (genéricas)",
			subtitle="Síntesis orientativa basada en los artefactos generados",
			bullets=[
				"La distribución geográfica sugiere focos de producción en países con mayor densidad de afiliaciones.",
				"El vocabulario más prominente refleja los ejes temáticos recurrentes y posibles líneas de investigación.",
				"La evolución temporal permite identificar períodos de crecimiento y temas en auge por revista/venue.",
				"Se recomienda complementar con análisis cualitativo de citas, coautorías y tópicos específicos.",
			],
		)

	logger.info(f"Informe PDF generado en: {out_pdf}")
	return 0


if __name__ == '__main__':
	raise SystemExit(main())

