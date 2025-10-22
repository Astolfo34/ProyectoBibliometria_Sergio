from __future__ import annotations

import os
import re
import time
import logging
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from typing import Iterable, Dict, List, Tuple

import matplotlib.pyplot as plt
import csv

# Logger y límites
logger = logging.getLogger("lineaTemporal")
MAX_CHARS: int = int(os.getenv("TIMELINE_MAX_CHARS", os.getenv("WORDCLOUD_MAX_CHARS", "10000000")))
TOP_JOURNALS: int = int(os.getenv("TIMELINE_TOP_JOURNALS", "5"))


def read_candidates(paths: Iterable[Path], max_chars: int | None = None) -> str:
	"""Lee y concatena contenido de archivos candidatos (.txt), con tope por caracteres.

	- Omite no .txt o inexistentes
	- Se detiene cuando alcanza `max_chars` si se provee
	"""
	limit = max_chars if max_chars and max_chars > 0 else None
	buf: List[str] = []
	total = 0
	files_ok = 0
	truncated = False
	for p in paths:
		if limit is not None and total >= limit:
			logger.info("Límite alcanzado; se detiene la lectura de más archivos.")
			break
		if not (p.is_file() and p.suffix.lower() == ".txt"):
			logger.debug(f"Omitido (no .txt/archivo): {p}")
			continue
		try:
			remaining = None if limit is None else max(0, limit - total)
			if remaining is None:
				content = p.read_text(encoding="utf-8", errors="ignore")
			else:
				with p.open("r", encoding="utf-8", errors="ignore") as f:
					content = f.read(remaining)
					if content and len(content) == remaining:
						truncated = True
			buf.append("\n" + (content or ""))
			total += len(content or "")
			files_ok += 1
			logger.info(f"Leído {p.name}: {len(content or '')} chars (acum={total})")
		except Exception as e:
			logger.warning(f"No se pudo leer {p}: {e}")
	if truncated:
		logger.warning("Contenido truncado por límite de caracteres.")
	logger.info(f"Archivos válidos leídos: {files_ok} | Caracteres acumulados: {total}")
	return "".join(buf)


def parse_entries_biblike(text: str) -> List[Dict[str, str]]:
	"""Parser sencillo de bloques BibTeX-like para extraer campos relevantes.

	Devuelve una lista de dicts con al menos: year (str), journal (str), booktitle (str).
	"""
	entries_raw = re.split(r"\n(?=@\w+\{)", text or "")
	parsed: List[Dict[str, str]] = []
	for entry in entries_raw:
		entry = entry.strip()
		if not entry:
			continue
		# Campos key = {value} | "value" | simple
		fields: Dict[str, str] = {}
		for m in re.finditer(r"(\w+)\s*=\s*(\{([^}]*)\}|\"([^\"]*)\"|([^,\n]+))\s*,?", entry, re.IGNORECASE):
			k = (m.group(1) or "").strip().lower()
			v = m.group(3) or m.group(4) or m.group(5) or ""
			fields[k] = v.strip()
		if not fields:
			continue
		parsed.append(fields)
	return parsed


def safe_year(yraw: str) -> int | None:
	if not yraw:
		return None
	m = re.search(r"\b(18|19|20|21)\d{2}\b", yraw)
	if not m:
		return None
	try:
		return int(m.group(0))
	except Exception:
		return None


def extract_year_journal(entries: List[Dict[str, str]]) -> List[Tuple[int, str]]:
	"""Extrae pares (year, journal_or_venue). Usa 'journal' o 'booktitle'; fallback 'unknown'."""
	data: List[Tuple[int, str]] = []
	for f in entries:
		y = safe_year(f.get("year", ""))
		if y is None:
			continue
		j = f.get("journal") or f.get("booktitle") or "unknown"
		j = re.sub(r"[{}\"]", "", j).strip()
		j = j if j else "unknown"
		data.append((y, j))
	return data


def counts_by_year(data: List[Tuple[int, str]]) -> Dict[int, int]:
	c = Counter()
	for y, _ in data:
		c[y] += 1
	return dict(sorted(c.items()))


def counts_by_year_journal(data: List[Tuple[int, str]]) -> Dict[int, Dict[str, int]]:
	m: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
	for y, j in data:
		m[y][j] += 1
	# ordenar interno por conteo desc
	out: Dict[int, Dict[str, int]] = {}
	for y, d in m.items():
		out[y] = dict(sorted(d.items(), key=lambda kv: kv[1], reverse=True))
	return dict(sorted(out.items()))


def select_top_journals(year_journal: Dict[int, Dict[str, int]], k: int) -> List[str]:
	total = Counter()
	for _, d in year_journal.items():
		total.update(d)
	return [j for j, _ in total.most_common(max(1, k))]


def plot_timeline(by_year: Dict[int, int], by_year_journal: Dict[int, Dict[str, int]], out_path: Path, top_k: int = 5) -> None:
	years = list(by_year.keys())
	totals = [by_year[y] for y in years]

	plt.figure(figsize=(14, 6))
	gs_rows = 1
	gs_cols = 2

	# Subplot 1: total por año
	ax1 = plt.subplot(gs_rows, gs_cols, 1)
	ax1.plot(years, totals, marker='o', linewidth=2, color='#1976D2')
	ax1.set_title('Publicaciones por año (total)')
	ax1.set_xlabel('Año')
	ax1.set_ylabel('Conteo')
	ax1.grid(True, alpha=0.3)

	# Subplot 2: top journals por año
	ax2 = plt.subplot(gs_rows, gs_cols, 2)
	top_j = select_top_journals(by_year_journal, top_k)
	palette = plt.cm.tab10.colors
	for i, j in enumerate(top_j):
		series = [by_year_journal.get(y, {}).get(j, 0) for y in years]
		ax2.plot(years, series, marker='o', linewidth=2, color=palette[i % len(palette)], label=j[:40])
	ax2.set_title(f'Publicaciones por año y revista (Top {len(top_j)})')
	ax2.set_xlabel('Año')
	ax2.set_ylabel('Conteo')
	ax2.grid(True, alpha=0.3)
	if top_j:
		ax2.legend(loc='upper left', fontsize=8)

	plt.tight_layout()
	out_path.parent.mkdir(parents=True, exist_ok=True)
	plt.savefig(out_path, dpi=200)
	plt.close()
	logger.info(f"Imagen de serie temporal guardada en: {out_path}")


def main() -> int:
	logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s', datefmt='%H:%M:%S')
	t0 = time.perf_counter()

	project_root = Path(__file__).resolve().parents[2]
	input_dir = project_root / "productosUnificados"
	candidate_files = [
		input_dir / "productos_unificados.txt",
		input_dir / "productosUnificados.txt",
	]

	logger.info("Leyendo candidatos para serie temporal (respetando límite de caracteres)…")
	raw = read_candidates(candidate_files, max_chars=MAX_CHARS)
	if not raw.strip():
		logger.error(f"No se encontraron contenidos en {input_dir}.")
		return 1

	logger.info("Parseando entradas BibTeX-like…")
	entries = parse_entries_biblike(raw)
	logger.info(f"Entradas parseadas: {len(entries)}")

	pairs = extract_year_journal(entries)
	if not pairs:
		logger.error("No se pudieron extraer pares (año, revista).")
		return 1

	by_year = counts_by_year(pairs)
	by_year_j = counts_by_year_journal(pairs)
	logger.info(f"Años con conteos: {len(by_year)} | Rango: {min(by_year)}-{max(by_year)} | Total publicaciones: {sum(by_year.values())}")

	timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
	out_dir = project_root / 'requerimiento5' / 'data' / 'data_lineaTemporal'
	out_img = out_dir / f'linea_temporal_{timestamp}.png'
	out_dir.mkdir(parents=True, exist_ok=True)

	# Exportar CSVs
	csv_year = out_dir / 'conteo_por_anio.csv'
	csv_year_journal = out_dir / 'conteo_por_anio_revista.csv'

	with open(csv_year, 'w', newline='', encoding='utf-8') as f:
		w = csv.writer(f)
		w.writerow(['year', 'count'])
		for y, c in sorted(by_year.items()):
			w.writerow([y, c])
	logger.info(f"CSV generado: {csv_year}")

	with open(csv_year_journal, 'w', newline='', encoding='utf-8') as f:
		w = csv.writer(f)
		w.writerow(['year', 'journal', 'count'])
		for y, d in sorted(by_year_j.items()):
			for j, c in d.items():
				w.writerow([y, j, c])
	logger.info(f"CSV generado: {csv_year_journal}")

	# Graficar
	plot_timeline(by_year, by_year_j, out_img, top_k=TOP_JOURNALS)

	logger.info(f"Duración total: {time.perf_counter() - t0:.2f}s")
	return 0


if __name__ == '__main__':
	raise SystemExit(main())

