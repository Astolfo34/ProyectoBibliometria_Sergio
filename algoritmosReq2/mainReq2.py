"""
Orquestación de algoritmos de similitud (Req2)

Flujo:
- Lee el grafo de citaciones desde Scripts grafo/salida_grafo/grafo_adj.json
- Muestra por consola (con colores) el TOP N (<=10) de autores más citados
- Pide al usuario ingresar dos textos a comparar
- Ejecuta algoritmos clásicos (Levenshtein, Jaccard, Cosine TF-IDF, Dice) y IA (Sentence-BERT)
- Guarda un CSV detallado en algoritmosReq2/data_req2
- Genera una imagen (gráfico vistoso) con los resultados por algoritmo
"""

from __future__ import annotations

import os
import re
import json
import time
import math
from datetime import datetime
from typing import Dict, Tuple, List

import matplotlib.pyplot as plt

# Dependencias opcionales: usaremos Rich si está disponible para una mejor UI, si no, caemos a print
try:
	from rich.console import Console
	from rich.table import Table
	from rich.panel import Panel
	from rich.prompt import IntPrompt, Prompt
	from rich.theme import Theme
	RICH_OK = True
except Exception:
	RICH_OK = False

try:
	import seaborn as sns
	SEABORN_OK = True
except Exception:
	SEABORN_OK = False

# Algoritmos clásicos y de IA
# Importar algoritmos soportando ejecución como script o como módulo
try:
	from algoritmosReq2.similarity_classical import (
		levenshtein_similarity,
		jaccard_similarity,
		cosine_tfidf_similarity,
		dice_similarity,
		jaccard_char_ngrams,
		dice_char_ngrams,
		cosine_tfidf_char,
	)
except Exception:
	from similarity_classical import (
		levenshtein_similarity,
		jaccard_similarity,
		cosine_tfidf_similarity,
		dice_similarity,
		jaccard_char_ngrams,
		dice_char_ngrams,
		cosine_tfidf_char,
	)

try:
	from algoritmosReq2.similarity_ai import semantic_similarity
	AI_OK = True
except Exception:
	try:
		from similarity_ai import semantic_similarity
		AI_OK = True
	except Exception:
		AI_OK = False


# --------------------------- Utilidades UI ---------------------------
def get_console() -> "Console | None":
	if not RICH_OK:
		return None
	theme = Theme(
		{
			"title": "bold magenta",
			"ok": "bold green",
			"warn": "bold yellow",
			"err": "bold red",
			"info": "cyan",
		}
	)
	return Console(theme=theme)


console = get_console()


def cprint(msg: str, style: str | None = None):
	if console:
		console.print(msg, style=style)
	else:
		print(msg)


# --------------------------- Carga de grafo ---------------------------
ROOT = os.path.dirname(os.path.dirname(__file__))
GRAFO_DIR = os.path.join(ROOT, "Scripts grafo", "salida_grafo")
GRAFO_JSON = os.path.join(GRAFO_DIR, "grafo_adj.json")


def cargar_grafo_adjacencia(path: str) -> Dict[str, Dict[str, float]]:
	if not os.path.isfile(path):
		raise FileNotFoundError(
			f"No se encontró el archivo de grafo en: {os.path.relpath(path, ROOT)}"
		)
	with open(path, "r", encoding="utf-8") as f:
		data = json.load(f)
	return data


def extraer_autor_de_nodo(nodo: str) -> str:
	"""
	Nodo típico: "Wang2024" => tomamos la parte alfabética inicial como autor (aprox. primer autor)
	Si no hay dígitos, devolvemos el nodo tal cual.
	"""
	m = re.match(r"([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)", nodo)
	return m.group(1) if m else nodo


def top_autores_mas_citados(adj: Dict[str, Dict[str, float]], n: int = 10) -> List[Tuple[str, float]]:
	"""
	Calcula la suma de citas entrantes por autor (aprox) excluyendo auto-citas perfectas (self-loop 1.0).
	"""
	# Construimos in-degree ponderado por nodo
	in_weight: Dict[str, float] = {}
	for src, vecinos in adj.items():
		for dst, w in vecinos.items():
			if src == dst:
				# ignorar self-loops puros (1.0) que vienen del armado del grafo
				continue
			in_weight[dst] = in_weight.get(dst, 0.0) + float(w)

	# Agregar por autor (primer autor aproximado por prefijo alfabético del id)
	autor_weight: Dict[str, float] = {}
	for nodo, w in in_weight.items():
		autor = extraer_autor_de_nodo(nodo)
		autor_weight[autor] = autor_weight.get(autor, 0.0) + w

	# Ordenar
	ordenado = sorted(autor_weight.items(), key=lambda x: x[1], reverse=True)
	return ordenado[: max(1, min(10, n))]


# ---------------------- Ejecución de algoritmos ----------------------
def ejecutar_algoritmos(text1: str, text2: str) -> Dict[str, float | None]:
	resultados: Dict[str, float | None] = {}

	def _simple_tokens(s: str) -> list[str]:
		return re.findall(r"\w+", (s or "").lower(), re.UNICODE)

	def _heuristic_char_n(a: str, b: str) -> int:
		la = len((a or "").strip())
		lb = len((b or "").strip())
		m = min(la, lb)
		if m <= 2:
			return 1
		if m <= 4:
			return 2
		return 3

	tok1, tok2 = _simple_tokens(text1), _simple_tokens(text2)
	short_texts = (len(tok1) < 3 and len(tok2) < 3)
	n_char = _heuristic_char_n(text1, text2)

	try:
		resultados["levenshtein"] = float(levenshtein_similarity(text1, text2))
	except Exception:
		resultados["levenshtein"] = None

	try:
		resultados["jaccard"] = float(jaccard_similarity(text1, text2))
	except Exception:
		resultados["jaccard"] = None

	# Cosine TF-IDF: palabra si hay tokens; si son muy cortos, usamos char n-grams
	try:
		if short_texts:
			resultados["cosine_tfidf"] = float(cosine_tfidf_char(text1, text2, n=n_char))
		else:
			ct = float(cosine_tfidf_similarity(text1, text2))
			# Si sale 0 por falta de vocabulario compartido y los textos son realmente cortos, probamos char
			if ct == 0.0 and (len(tok1) < 5 or len(tok2) < 5):
				ct = float(cosine_tfidf_char(text1, text2, n=n_char))
			resultados["cosine_tfidf"] = ct
	except Exception:
		resultados["cosine_tfidf"] = None

	try:
		resultados["dice"] = float(dice_similarity(text1, text2))
	except Exception:
		resultados["dice"] = None

	# Métricas por n-gramas de caracteres (heurística de n)
	try:
		resultados["jaccard_char"] = float(jaccard_char_ngrams(text1, text2, n=n_char))
	except Exception:
		resultados["jaccard_char"] = None
	try:
		resultados["dice_char"] = float(dice_char_ngrams(text1, text2, n=n_char))
	except Exception:
		resultados["dice_char"] = None

	if AI_OK:
		try:
			resultados["semantic_sbert"] = float(semantic_similarity(text1, text2))
		except Exception:
			resultados["semantic_sbert"] = None
	else:
		resultados["semantic_sbert"] = None

	# Guardamos el n de char-ngrams usado (para logging/CSV)
	resultados["char_ngram_n"] = n_char
	return resultados


# --------------------------- Persistencia ---------------------------
DATA_DIR = os.path.join(ROOT, "algoritmosReq2", "data_req2")
os.makedirs(DATA_DIR, exist_ok=True)


def guardar_csv(text1: str, text2: str, resultados: Dict[str, float | None]) -> str:
	import csv

	ts = datetime.now().strftime("%Y%m%d_%H%M%S")
	csv_path = os.path.join(DATA_DIR, f"similarity_results_{ts}.csv")

	campos = [
		"timestamp",
		"text1",
		"text2",
		"len_text1",
		"len_text2",
		"levenshtein",
		"jaccard",
		"cosine_tfidf",
		"dice",
		"jaccard_char",
		"dice_char",
		"char_ngram_n",
		"semantic_sbert",
	]

	with open(csv_path, "w", newline="", encoding="utf-8") as f:
		writer = csv.DictWriter(f, fieldnames=campos)
		writer.writeheader()
		writer.writerow(
			{
				"timestamp": ts,
				"text1": text1,
				"text2": text2,
				"len_text1": len(text1 or ""),
				"len_text2": len(text2 or ""),
				"levenshtein": resultados.get("levenshtein"),
				"jaccard": resultados.get("jaccard"),
				"cosine_tfidf": resultados.get("cosine_tfidf"),
				"dice": resultados.get("dice"),
				"semantic_sbert": resultados.get("semantic_sbert"),
				"jaccard_char": resultados.get("jaccard_char"),
				"dice_char": resultados.get("dice_char"),
				"char_ngram_n": resultados.get("char_ngram_n"),
			}
		)

	return csv_path


# --------------------------- Visualización ---------------------------
def plot_resultados(resultados: Dict[str, float | None]) -> str:
	ts = datetime.now().strftime("%Y%m%d_%H%M%S")
	img_path = os.path.join(DATA_DIR, f"similarity_plot_{ts}.png")

	# Preparamos datos normalizados 0-1 (si None -> 0)
	labels = [
		"Levenshtein",
		"Jaccard (word)",
		"Cosine TF-IDF",
		"Dice (word)",
		"Jaccard (char)",
		"Dice (char)",
		"Semantic SBERT",
	]
	keys = [
		"levenshtein",
		"jaccard",
		"cosine_tfidf",
		"dice",
		"jaccard_char",
		"dice_char",
		"semantic_sbert",
	]
	values = [resultados.get(k) if resultados.get(k) is not None else 0.0 for k in keys]

	# Radar chart vistoso
	angles = [n / float(len(labels)) * 2 * math.pi for n in range(len(labels))]
	values_cycle = values + values[:1]
	angles_cycle = angles + angles[:1]

	plt.figure(figsize=(8, 8))
	ax = plt.subplot(111, polar=True)
	ax.set_theta_offset(math.pi / 2)
	ax.set_theta_direction(-1)

	# Grilla y etiquetas
	plt.xticks(angles, labels, color="#222", fontsize=10)
	ax.set_rlabel_position(0)
	yticks = [0.2, 0.4, 0.6, 0.8, 1.0]
	plt.yticks(yticks, [str(y) for y in yticks], color="#555", fontsize=9)
	plt.ylim(0, 1)

	# Paleta
	color = "#7b5cd6"  # violeta agradable
	ax.plot(angles_cycle, values_cycle, linewidth=2, linestyle="-", color=color)
	ax.fill(angles_cycle, values_cycle, color=color, alpha=0.25)

	plt.title("Grado de similitud por algoritmo", fontsize=14, fontweight="bold")
	plt.tight_layout()
	plt.savefig(img_path, dpi=150)
	plt.close()
	return img_path


# --------------------------- Manual PDF ---------------------------
def generar_manual_pdf() -> str:
	from matplotlib.backends.backend_pdf import PdfPages

	ts = datetime.now().strftime("%Y%m%d_%H%M%S")
	pdf_path = os.path.join(DATA_DIR, f"manual_algoritmos_req2_{ts}.pdf")

	def _page(title: str, sections: List[Tuple[str, str]], facecolor: str = "#ffffff"):
		fig = plt.figure(figsize=(8.27, 11.69), facecolor=facecolor)  # A4
		ax = plt.gca()
		ax.axis('off')

		# Márgenes y envoltura conservadora para evitar cortes laterales
		left_x = 0.10
		right_x = 0.90
		text_width_chars = 90  # ancho conservador en caracteres para no desbordar

		import textwrap

		y = 0.95
		fig.text(0.5, y, title, ha='center', va='top', fontsize=20, fontweight='bold', color="#333")
		y -= 0.05
		for subtitle, body in sections:
			# Subtítulo centrado para mejorar composición
			fig.text(0.5, y, subtitle, ha='center', va='top', fontsize=13, fontweight='bold', color="#5533aa")
			y -= 0.035

			wrapped = textwrap.fill(body, width=text_width_chars)
			for ln in wrapped.splitlines():
				fig.text(left_x, y, ln, ha='left', va='top', fontsize=11, color="#222")
				y -= 0.022
			y -= 0.015

	with PdfPages(pdf_path) as pdf:
		_page(
			"Manual de algoritmos de similitud (Req2)",
			[
				("Descripción",
				 "Este documento resume la base matemática, relación con el análisis bibliométrico e interpretación de los valores (0–1) de los algoritmos implementados para comparar pares de textos (títulos/abstracts)."),
				("Rango de valores",
				 "En todas las métricas: 0.0 indica sin similitud y 1.0 indica textos idénticos. Valores intermedios reflejan similitud parcial."),
			],
			facecolor="#f7f5ff",
		); pdf.savefig(); plt.close()

		_page(
			"Levenshtein (similitud)",
			[
				("Fórmula",
				 "sim = 1 - (distancia_levenshtein(a,b) / max(len(a), len(b))). Mide el mínimo número de ediciones (inserción/eliminación/sustitución) para transformar a→b."),
				("Relación con el análisis",
				 "Útil para detectar versiones casi idénticas de títulos o pequeñas variaciones tipográficas. Sensible a longitud."),
				("Interpretación",
				 "Cercano a 1: textos casi iguales. Cercano a 0: textos muy diferentes."),
			],
		); pdf.savefig(); plt.close()

		_page(
			"Jaccard (palabras)",
			[
				("Fórmula",
				 "J(A,B) = |A ∩ B| / |A ∪ B|, donde A y B son conjuntos de palabras normalizadas."),
				("Relación con el análisis",
				 "Capta solapamiento de vocabulario clave en títulos/abstracts. No considera frecuencia ni orden."),
				("Interpretación",
				 "0: vocabulario disjunto. 1: mismo conjunto de palabras."),
			],
		); pdf.savefig(); plt.close()

		_page(
			"Dice (palabras)",
			[
				("Fórmula",
				 "Dice(A,B) = 2|A ∩ B| / (|A| + |B|). Métrica similar a Jaccard pero con diferente ponderación."),
				("Relación con el análisis",
				 "Comparación de vocabularios con énfasis en coincidencias comunes."),
				("Interpretación",
				 "Valores más altos indican mayor solapamiento léxico."),
			],
		); pdf.savefig(); plt.close()

		_page(
			"Cosine TF-IDF",
			[
				("Fórmula",
				 "cos(v1,v2) = (v1·v2) / (||v1||·||v2||), donde v1 y v2 son vectores TF-IDF (palabras o n-gramas de caracteres)."),
				("Relación con el análisis",
				 "Mide similitud basada en términos discriminativos. Para textos muy cortos usamos n-gramas de caracteres (heurística)."),
				("Interpretación",
				 "Alto cuando los términos relevantes son compartidos en proporciones similares."),
			],
		); pdf.savefig(); plt.close()

		_page(
			"Jaccard (caracteres n-gram)",
			[
				("Fórmula",
				 "J(Cn(a), Cn(b)) = |Cn(a) ∩ Cn(b)| / |Cn(a) ∪ Cn(b)|, con Cn(x) los n-gramas de caracteres de x."),
				("Relación con el análisis",
				 "Robusto en textos cortos o con pequeñas variaciones morfológicas/ortográficas. n se ajusta por heurística según longitud."),
				("Interpretación",
				 "Mayor valor indica mayor superposición de n-gramas de caracteres."),
			],
		); pdf.savefig(); plt.close()

		_page(
			"Dice (caracteres n-gram)",
			[
				("Fórmula",
				 "Dice(Cn(a),Cn(b)) = 2|Cn(a) ∩ Cn(b)| / (|Cn(a)| + |Cn(b)|)."),
				("Relación con el análisis",
				 "Complementa Jaccard a nivel de caracteres; útil para títulos cortos."),
				("Interpretación",
				 "Cercano a 1 cuando los fragmentos de caracteres coinciden fuertemente."),
			],
		); pdf.savefig(); plt.close()

		_page(
			"Semantic SBERT",
			[
				("Base",
				 "Embeddings de frases (Sentence-BERT). Similitud coseno entre vectores de alta dimensión que capturan semántica."),
				("Relación con el análisis",
				 "Detecta similitud semántica más allá de palabras exactas; muy útil para abstracts."),
				("Interpretación",
				 ">0.8 típicamente indica alta cercanía semántica; 0.5–0.8 similaridades temáticas parciales; <0.5 escasa relación."),
			],
		); pdf.savefig(); plt.close()

	return pdf_path

# ------------------------------ Main ------------------------------
def main():
	# Header
	cprint("\n╔════════════════════════════════════════════════════════════╗", "title")
	cprint("  ORQUESTACIÓN DE ALGORITMOS DE SIMILITUD (Req2)", "title")
	cprint("╚════════════════════════════════════════════════════════════╝\n", "title")

	# Cargar grafo
	try:
		adj = cargar_grafo_adjacencia(GRAFO_JSON)
		cprint("✔ Grafo de citaciones cargado.", "ok")
	except Exception as e:
		cprint(f"⚠ No se pudo cargar el grafo de citaciones: {e}", "warn")
		adj = {}

	# Top N autores
	N = 10
	if console:
		try:
			N = IntPrompt.ask("Indica N para TOP autores (1-10)", default=10)
			N = max(1, min(10, int(N)))
		except Exception:
			N = 10
	else:
		try:
			N = int(input("Indica N para TOP autores (1-10) [10]: ") or "10")
			N = max(1, min(10, N))
		except Exception:
			N = 10

	if adj:
		top_autores = top_autores_mas_citados(adj, N)
		if console:
			table = Table(show_header=True, header_style="bold blue")
			table.add_column("Rank", justify="right")
			table.add_column("Autor (aprox.)", justify="left")
			table.add_column("Citas (ponderadas)", justify="right")
			for i, (autor, w) in enumerate(top_autores, start=1):
				table.add_row(str(i), autor, f"{w:.3f}")
			console.print(Panel(table, title="TOP autores más citados (según grafo)", border_style="cyan"))
		else:
			print("TOP autores más citados (según grafo):")
			for i, (autor, w) in enumerate(top_autores, start=1):
				print(f"{i:2d}. {autor:20s}  {w:.3f}")
	else:
		cprint("No hay grafo cargado. Se omitirá el TOP de autores.", "warn")

	# Pedir textos (validando que no estén vacíos)
	cprint("\nIngresa los textos a comparar:", "info")
	def _ask_pair() -> tuple[str, str]:
		if console:
			t1 = Prompt.ask("[bold]Texto 1[/bold]")
			t2 = Prompt.ask("[bold]Texto 2[/bold]")
		else:
			t1 = input("Texto 1: ")
			t2 = input("Texto 2: ")
		return (t1 or "").strip(), (t2 or "").strip()

	text1, text2 = _ask_pair()
	attempt = 0
	while (not text1) or (not text2):
		attempt += 1
		cprint("Los textos no pueden estar vacíos. Inténtalo nuevamente.", "warn")
		if attempt >= 2:
			cprint("Sugerencia: pega títulos o resúmenes para obtener valores > 0.", "info")
		text1, text2 = _ask_pair()

	# Ejecutar algoritmos
	cprint("\nEjecutando algoritmos de similitud...", "info")
	t0 = time.time()
	resultados = ejecutar_algoritmos(text1, text2)
	dt = time.time() - t0

	# Mostrar resultados (ocultando campos de configuración auxiliares)
	if console:
		table_r = Table(show_header=True, header_style="bold green")
		table_r.add_column("Algoritmo")
		table_r.add_column("Score", justify="right")
		for k, v in resultados.items():
			if k == "char_ngram_n":
				continue
			score = "N/A" if v is None else f"{v:.4f}"
			table_r.add_row(k, score)
		console.print(Panel(table_r, title=f"Resultados (tiempo: {dt:.2f}s)", border_style="green"))
	else:
		print(f"Resultados (tiempo: {dt:.2f}s):")
		for k, v in resultados.items():
			if k == "char_ngram_n":
				continue
			print(f" - {k:15s}: {('N/A' if v is None else f'{v:.4f}')}" )

	# Guardar CSV
	csv_path = guardar_csv(text1, text2, resultados)
	cprint(f"\n✔ CSV guardado en: {os.path.relpath(csv_path, ROOT)}", "ok")

	# Generar imagen
	try:
		img_path = plot_resultados(resultados)
		cprint(f"✔ Imagen generada en: {os.path.relpath(img_path, ROOT)}", "ok")
	except Exception as e:
		cprint(f"⚠ No se pudo generar la imagen: {e}", "warn")

	# Generar manual PDF
	try:
		manual_path = generar_manual_pdf()
		cprint(f"✔ Manual PDF generado en: {os.path.relpath(manual_path, ROOT)}", "ok")
	except Exception as e:
		cprint(f"⚠ No se pudo generar el manual PDF: {e}", "warn")

	# Tips de dependencias
	if not AI_OK:
		cprint(
			"Nota: similitud semántica (SBERT) no disponible. Revisa que `sentence-transformers` esté instalado.",
			"warn",
		)
	if not RICH_OK:
		cprint("Nota: interfaz enriquecida no disponible (paquete rich no instalado).", "warn")
	if not SEABORN_OK:
		cprint("Nota: para estilos adicionales instala `seaborn`.", "info")


if __name__ == "__main__":
	main()

