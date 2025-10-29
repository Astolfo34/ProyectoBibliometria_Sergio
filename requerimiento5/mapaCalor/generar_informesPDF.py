from __future__ import annotations

import os
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

