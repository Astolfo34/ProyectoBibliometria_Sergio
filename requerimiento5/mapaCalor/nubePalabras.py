from __future__ import annotations

import os
import re
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Iterable, Set, List

import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

# Logger de módulo
logger = logging.getLogger("nubePalabras")

# Límite máximo de caracteres a procesar (por defecto 10 millones). Se puede
# sobreescribir con la variable de entorno WORDCLOUD_MAX_CHARS.
MAX_CHARS: int = int(os.getenv("WORDCLOUD_MAX_CHARS", "10000000"))


def read_txt_files(paths: Iterable[Path], max_chars: int | None = None) -> str:
	"""Read and concatenate .txt files as UTF-8, extracting only abstracts and normalizing whitespace.

	- Skips files that don't exist or are not .txt.
	- Stops early when reaching `max_chars` total characters (if provided).
	- Normalizes whitespace after each read chunk.
	"""
	limit = max_chars if max_chars and max_chars > 0 else None
	texts: list[str] = []
	files_ok = 0
	total_chars = 0
	truncated = False
	total_abstracts = 0

	for p in paths:
		if limit is not None and total_chars >= limit:
			logger.info("Se alcanzó el límite de caracteres; se detiene la lectura de más archivos.")
			break
		try:
			if p.is_file() and p.suffix.lower() == ".txt":
				logger.info(f"Leyendo archivo: {p}")
				remaining = None if limit is None else max(0, limit - total_chars)
				if remaining == 0:
					logger.debug("No quedan caracteres disponibles para leer.")
					break

				if remaining is None:
					# Leer todo el archivo
					content = p.read_text(encoding="utf-8", errors="ignore")
				else:
					# Leer hasta 'remaining' caracteres para no exceder el límite de lectura
					with p.open("r", encoding="utf-8", errors="ignore") as f:
						content = f.read(remaining)
						# Si el archivo es mayor, marcamos truncamiento de lectura
						if content and len(content) == remaining:
							truncated = True

				logger.debug(f"Tamaño leído (caracteres) en {p.name}: {len(content) if content else 0}")
				# Extraer solo abstracts del contenido leído
				abstracts = extract_abstracts_from_text(content or "")
				logger.info(f"Abstracts extraídos de {p.name}: {len(abstracts)}")
				total_abstracts += len(abstracts)
				content_abs = re.sub(r"\s+", " ", "\n".join(abstracts))

				# Aplicar límite por caracteres en la concatenación final
				if limit is not None and total_chars + len(content_abs) > limit:
					remaining_concat = limit - total_chars
					if remaining_concat > 0:
						texts.append(content_abs[:remaining_concat])
						total_chars += remaining_concat
					truncated = True
					logger.info("Se alcanzó el límite de caracteres durante la concatenación; se detiene.")
					files_ok += 1
					break
				else:
					texts.append(content_abs)
					files_ok += 1
					total_chars += len(content_abs)
				if limit is not None and total_chars >= limit:
					logger.info("Se alcanzó el límite de caracteres durante la lectura; se detiene.")
					break
			else:
				logger.debug(f"Omitido (no .txt o no es archivo): {p}")
		except Exception as e:
			# Ignore unreadable files; continue with others
			logger.warning(f"No se pudo leer {p}: {e}")
			continue

	if truncated:
		logger.warning("El contenido fue truncado para respetar el límite de caracteres.")
	logger.info(f"Archivos válidos leídos: {files_ok} | Abstracts totales: {total_abstracts} | Caracteres acumulados: {total_chars}")
	return "\n".join(texts)


def extract_abstracts_from_text(text: str) -> List[str]:
	"""Extract abstract sections from raw text using simple header/stopper heuristics.

	Heuristics:
	- Start when a line begins with 'Abstract', 'Resumen' o 'Summary' (insensible a mayúsculas), opcional ':' '.' '-' '—'.
	- Stop on blank line OR when a new section header appears (Keywords, Palabras clave, Index terms, Introduction, References, Acknowledg*, Conclusion* ...).
	- Ignore very short extracts (< 30 chars).
	"""
	headers = re.compile(r"^\s*(abstract|resumen|summary)\b\s*[:.\-–—]?\s*(.*)$", re.IGNORECASE)
	stoppers = re.compile(
		r"^\s*(keywords|palabras\s*clave|index\s*terms|introduction|references|acknowledg|conclusion|resumen|abstract)\b",
		re.IGNORECASE,
	)
	abstracts: List[str] = []
	lines = (text or "").splitlines()
	i = 0
	while i < len(lines):
		line = lines[i].strip()
		m = headers.match(line)
		if m:
			# Rest of the header line after the label
			rest = m.group(2).strip()
			buff: List[str] = []
			if rest:
				buff.append(rest)
			i += 1
			while i < len(lines):
				l = lines[i].strip()
				if not l:
					# break on first blank line to avoid spilling into next sections
					break
				if stoppers.match(l):
					break
				buff.append(l)
				i += 1
			abs_text = " ".join(buff)
			if len(abs_text) >= 30:
				abstracts.append(abs_text)
			continue  # do not i+=1 to avoid skipping the stopper line processing
		i += 1
	return abstracts


def build_stopwords() -> Set[str]:
	"""Return a combined set of English + Spanish stopwords and common noise terms."""
	es_stopwords = {
		# Common Spanish stopwords (subset + extras for bibliographic text)
		"de","la","que","el","en","y","a","los","del","se","las","por","un","para","con","no","una",
		"su","al","lo","como","más","pero","sus","le","ya","o","este","sí","porque","esta","entre","cuando",
		"muy","sin","sobre","también","me","hasta","hay","donde","quien","desde","todo","nos","durante","todos",
		"uno","les","ni","contra","otros","ese","eso","ante","ellos","e","esto","mí","antes","algunos","qué",
		"unos","yo","otro","otras","otra","él","tanto","esa","estos","mucho","quienes","nada","muchos","cual",
		"poco","ella","estar","estas","algunas","algo","nosotros","mi","mis","tú","te","ti","tu","tus","ellas",
		"nosotras","vosotros","vosotras","os","mío","mía","míos","mías","tuyo","tuya","tuyos","tuyas","suyo",
		"suya","suyos","suyas","nuestro","nuestra","nuestros","nuestras","vuestro","vuestra","vuestros","vuestras",
		"esos","esas","estoy","estás","está","estamos","estáis","están","esté","estés","estemos","estéis",
		"estén","estaré","estarás","estará","estaremos","estaréis","estarán","estaría","estarías","estaríamos",
		"estaríais","estarían","estaba","estabas","estábamos","estabais","estaban","estuve","estuviste","estuvo",
		"estuvimos","estuvisteis","estuvieron","estuviera","estuvieras","estuviéramos","estuvierais","estuvieran",
		"estuviese","estuvieses","estuviésemos","estuvieseis","estuviesen","siendo","sido","soy","eres","es","somos",
		"sois","son","sea","seas","seamos","seáis","sean","seré","serás","será","seremos","seréis","serán",
		"sería","serías","seríamos","seríais","serían","tengo","tienes","tiene","tenemos","tenéis","tienen","tenga",
		"tengas","tengamos","tengáis","tengan","tendré","tendrás","tendrá","tendremos","tendréis","tendrán","tendría",
		"tendrías","tendríamos","tendríais","tendrían","bibliometría","artículo","artículos","paper","papers","doi",
		"https","http","www","vol","pp","et","al","figure","table","springer","ieee","sciencedirect","abstract"
	}
	common_noise = {
		# Extra tokens often present in merged bib -> txt exports
		"keywords","introduction","results","discussion","conclusion","references","available","online","license",
		"copyright","rights","reserved","publication","authors","author","journal","issue","volume","number"
	}
	# Combine with WordCloud's default English stopwords
	combined = set(STOPWORDS) | es_stopwords | common_noise
	logger.info(
		f"Stopwords: EN(defecto)={len(STOPWORDS)} | ES(custom)={len(es_stopwords)} | comunes={len(common_noise)} | total={len(combined)}"
	)
	return combined


def clean_text(text: str) -> str:
	"""Basic cleaning: lowercasing and removing URLs; keep punctuation to let WordCloud tokenize."""
	text = text.lower()
	text = re.sub(r"https?://\S+", " ", text)
	text = re.sub(r"www\.[^\s]+", " ", text)
	return text


def generate_wordcloud(text: str, stopwords: Set[str]) -> WordCloud:
	logger.info("Generando nube de palabras…")
	# Solo considerar palabras (ya en minúscula) de 3+ letras (ES/EN), evitando dígitos y 1-2 letras
	word_regexp = r"[a-záéíóúüñ]{3,}"
	logger.debug(f"Expresión regular de tokens: {word_regexp}")
	return WordCloud(
		width=1600,
		height=1000,
		background_color="white",
		stopwords=stopwords,
		collocations=False,  # evitar bigramas dominantes
		max_words=250,       # reducir densidad para mejor legibilidad
		prefer_horizontal=0.9,
		max_font_size=120,   # limitar tamaño máximo de fuente
		min_font_size=8,     # evitar letras demasiado pequeñas
		scale=2,             # mayor resolución de salida
		normalize_plurals=True,
		random_state=42,
		regexp=word_regexp,
	).generate(text)


	
def save_wordcloud_image(wc: WordCloud, out_path: Path) -> None:
	out_path.parent.mkdir(parents=True, exist_ok=True)
	plt.figure(figsize=(16, 10))
	plt.imshow(wc, interpolation="bilinear")
	plt.axis("off")
	plt.tight_layout(pad=0)
	plt.savefig(out_path, dpi=200)
	plt.close()
	logger.info(f"Imagen guardada en: {out_path}")


def main() -> int:
	# Configurar logging (por defecto INFO)
	logging.basicConfig(
		level=logging.INFO,
		format="[%(asctime)s] %(levelname)s - %(message)s",
		datefmt="%H:%M:%S",
	)
	start_total = time.perf_counter()

	# Project root inferred from this file location: .../requerimiento5/mapaCalor/nubePalabras.py
	project_root = Path(__file__).resolve().parents[2]
	logger.info(f"Raíz del proyecto: {project_root}")

	input_dir = project_root / "productosUnificados"
	# Consider both file name variants provided
	candidate_files = [
		input_dir / "productos_unificados.txt",
		input_dir / "productosUnificados.txt",
	]
	logger.info("Recolectando SOLO abstracts desde archivos candidatos…")
	for cf in candidate_files:
		logger.debug(f"Candidato: {cf}")

	text = read_txt_files(candidate_files, max_chars=MAX_CHARS)
	if not text.strip():
		logger.error(
			f"No se encontraron contenidos en {input_dir}. Asegúrate de que existan archivos .txt."
		)
		return 1

	logger.info("Limpiando texto…")
	len_before = len(text)
	text = clean_text(text)
	len_after = len(text)
	logger.info(f"Limpieza completada. Caracteres: antes={len_before} -> después={len_after}")
	stopwords = build_stopwords()

	gen_start = time.perf_counter()
	wc = generate_wordcloud(text, stopwords)
	gen_dur = time.perf_counter() - gen_start
	logger.info(f"Nube generada en {gen_dur:.2f}s")

	# Mostrar top términos para trazabilidad
	try:
		top_terms = sorted(wc.words_.items(), key=lambda kv: kv[1], reverse=True)[:15]
		formatted = ", ".join(f"{w}:{f:.3f}" for w, f in top_terms)
		logger.info(f"Top 15 términos: {formatted}")
	except Exception as e:
		logger.debug(f"No se pudieron extraer términos principales: {e}")

	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	output_dir = project_root / "requerimiento5" / "data" / "data_nubePalabras"
	out_file = output_dir / f"nube_palabras_{timestamp}.png"
	save_wordcloud_image(wc, out_file)

	logger.info(f"Nube de palabras generada correctamente.")
	logger.info(f"Archivo de salida: {out_file}")
	logger.info(f"Duración total: {time.perf_counter() - start_total:.2f}s")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

