
import os
import subprocess
import sys
import glob
import time
import threading
from pathlib import Path
from getpass import getpass
# Nota: Evitamos importar bibliotecas externas a nivel de módulo para no fallar
# antes de configurar/instalar el entorno. Se importan de forma diferida.

from utils.unificar import unificar

# ========================== CLI Styling (Rich) ==========================
try:
	from rich.console import Console
	from rich.panel import Panel
	from rich.table import Table
	from rich.prompt import Prompt
	from rich.theme import Theme
	RICH_OK = True
except Exception:
	RICH_OK = False


def _get_console() -> "Console | None":
	if not RICH_OK:
		return None
	theme = Theme(
		{
			"title": "bold magenta",
			"ok": "bold green",
			"warn": "bold yellow",
			"err": "bold red",
			"info": "cyan",
			"muted": "#888888",
		}
	)
	return Console(theme=theme)


console = _get_console()


def cprint(msg: str, style: str | None = None):
	if console:
		console.print(msg, style=style)
	else:
		print(msg)


def _panel(title: str, body: str, style: str = "info"):
	if console:
		console.print(Panel.fit(body, title=title, border_style=style))
	else:
		print(f"\n=== {title} ===\n{body}\n")


def _table(title: str, columns: list[str], rows: list[list[str | int | float]]):
	if not console:
		# Fallback simple
		print(f"\n{title}")
		print(" | ".join(columns))
		for r in rows:
			print(" | ".join(str(x) for x in r))
		return
	table = Table(title=title, style="info")
	for col in columns:
		table.add_column(str(col))
	for row in rows:
		table.add_row(*[str(x) for x in row])
	console.print(table)

# Configuración y constantes
URL_BIBLIOTECA = "https://library.uniquindio.edu.co/databases"  # Mantener la URL general
NOMBRES_BASES = ["Springer", "ScienceDirect", "IEEE"]
TERMINOS_BUSQUEDA = ["generative artificial intelligence","Computational Thinking", "AI in Education"]
CARPETA_DATA = "data"

def _show_intro_messages():
	"""Muestra los mensajes solicitados al iniciar la aplicación usando estilos de consola."""
	bienvenidos = (
		"Binvenidos: Este es el proyecto de bibliometria de analisis de algoritmos con la base de datos de la Universidad del Quindio. "
		"Tenga en cuenta usar el correo con el cual tiene acceso a la biblioteca crai de la Universidad. "
		"Los articulos seran extraidos considerando las busquedas (\"generative artificial intelligence\",\"Computational Thinking\", \"AI in Education\"), "
		"y seran extraidos de las bases de datos (\"Springer\", \"ScienceDirect\", \"IEEE\") para su analisi."
	)
	sugerencia = (
		"Sugerencia: este metodo es unicamente regulado por su usuario, tome en cuenta que el proceso de escapeo es demorado si es la primera vez que lo ejecuta, "
		"al rededor de 40-60 mins. De haber datos ya extaridos , el sistema continuara con los demas requerimientos."
	)
	advertencia = (
		"Advertencia: Sus credenciales seran tomadas por cada ejecucion y no serna almacenadas en los repositorios del proyecto, "
		"ya que seran tomadas como variables de entorno. si el Programa falla en este paso considere que sus credenciales sean correctas."
	)

	_panel("Bienvenida", bienvenidos, style="title")
	_panel("Sugerencia", sugerencia, style="warn")
	_panel("Advertencia", advertencia, style="err")


def _ensure_env_with_credentials():
	"""Solicita credenciales por terminal y crea/actualiza el archivo .env en el root del repo.

	No modifica la forma en que otros módulos leen las variables; únicamente garantiza que
	exista el archivo .env con EMAIL y PASSWORD actualizados.
	"""
	repo_root = Path(__file__).resolve().parent
	env_path = repo_root / ".env"

	# Pedir credenciales por terminal (ocultar contraseña)
	if RICH_OK and console:
		email = Prompt.ask("Ingrese su correo institucional (biblioteca CRAI)")
		cprint("Ingrese su contraseña (no se mostrará al escribir):", "muted")
		password = getpass("")
	else:
		email = input("Ingrese su correo institucional (biblioteca CRAI): ")
		password = getpass("Ingrese su contraseña: ")

	# Construir contenido del .env según referencia del proyecto
	content_lines = [
		"# Archivo de variables sensibles para el proyecto",
		f"EMAIL={email}",
		f"PASSWORD={password}",
		"",
	]
	try:
		with open(env_path, "w", encoding="utf-8") as f:
			f.write("\n".join(content_lines))
		_panel("Credenciales", f"Se guardaron/actualizaron las credenciales en '{env_path.name}'.", style="ok")
	except Exception as e:
		_panel("Error", f"No fue posible escribir el archivo .env: {e}", style="err")
		raise

def check_and_setup_env():
	"""Garantiza un entorno funcional y dependencias instaladas.
	- Si no existe venv o está corrupto, crea uno con `python -m venv venv`.
	- Instala/actualiza dependencias desde `config/requirements.txt` usando el Python del venv.
	- Si estamos ejecutando con otro intérprete, relanza el script con el Python del venv.
	"""
	repo_root = Path(__file__).resolve().parent
	venv_dir = repo_root / "venv"
	venv_python = venv_dir / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")

	needs_create = (not venv_dir.exists()) or (not venv_python.exists())
	if needs_create:
		_panel("Entorno", "Creando entorno virtual (venv)...", style="warn")
		subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

	py_exec = str(venv_python if venv_python.exists() else Path(sys.executable))

	# Instalar requerimientos
	try:
		subprocess.run([py_exec, "-m", "pip", "install", "--upgrade", "pip"], check=True)
		req = repo_root / "config" / "requirements.txt"
		if req.exists():
			_panel("Dependencias", f"Instalando desde {req}...", style="info")
			subprocess.run([py_exec, "-m", "pip", "install", "-r", str(req)], check=True)
		else:
			subprocess.run([py_exec, "-m", "pip", "install", "rich", "bibtexparser"], check=False)
	except subprocess.CalledProcessError as e:
		_panel("Dependencias", f"Fallo al instalar dependencias (code {e.returncode}).", style="err")
		raise

	# Si no estamos usando el python del venv, relanzar proceso con ese intérprete
	if venv_python.exists() and Path(sys.executable) != venv_python:
		_panel("Reinicio", f"Reejecutando con entorno: {venv_python}", style="warn")
		os.execv(str(venv_python), [str(venv_python), __file__])

def hay_bibtex_validos(carpeta_data: str = CARPETA_DATA) -> bool:
	"""Devuelve True si existen archivos .bib parseables con al menos una entrada."""
	pattern = os.path.join(carpeta_data, "*.bib")
	archivos = glob.glob(pattern)
	if not archivos:
		return False
	for bib in archivos:
		try:
			# Import lazy (después de check_and_setup_env)
			import bibtexparser  # noqa: WPS433 (carga tardía intencional)
			with open(bib, encoding="utf-8") as f:
				db = bibtexparser.load(f)
				if getattr(db, "entries", None):
					return True
		except Exception:
			continue
	return False


def ejecutar_scraping():
	import shutil
	import time
	# Importar dependencias que requieren paquetes externos aquí, después de preparar el entorno
	from selenium_scripts.selenium_setup import configurar_driver
	from selenium_scripts.navigation import (
		login_portal_universidad,
		obtener_enlaces_bases,
		buscar_en_base,
		validar_con_google,
	)
	from scraping.scraping import extraer_articulos, guardar_articulos_bibtex
	from html_structure.save_html_selenium import save_html

	driver, temp_profile_dir = configurar_driver()
	try:
		cprint("[Portal] Ingresando al portal de la universidad...", "info")
		driver.get(URL_BIBLIOTECA)
		time.sleep(2)
		save_html(driver, "web_portal_universidad", "index.html")
		enlaces_bases = obtener_enlaces_bases(driver, NOMBRES_BASES)
		cprint(f"Enlaces obtenidos: {enlaces_bases}", "muted")
		for base, url_base in enlaces_bases.items():
			for termino in TERMINOS_BUSQUEDA:
				cprint(f"[{base}] Buscando el término '{termino}'...", "info")
				driver.get(url_base)
				time.sleep(2)
				save_html(driver, f"{base}_html", f"home_{base}.html")

				# Validar credenciales antes de continuar
				validar_con_google(driver)

				# Intentar login solo si aparece el formulario
				try:
					from selenium.webdriver.common.by import By
					from selenium.webdriver.support.ui import WebDriverWait
					from selenium.webdriver.support import expected_conditions as EC
					WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "username")))
					login_portal_universidad(driver)
					time.sleep(2)
					save_html(driver, f"{base}_html", f"login_{base}.html")
				except Exception:
					pass

				buscar_en_base(driver, url_base, base, termino)
				time.sleep(2)
				save_html(driver, f"{base}_html", f"resultados_{base}_{termino.replace(' ', '_')}.html")
				articulos = extraer_articulos(driver, base, max_resultados=1000)
				guardar_articulos_bibtex(articulos, base, termino, CARPETA_DATA)
	finally:
		driver.quit()
		shutil.rmtree(temp_profile_dir, ignore_errors=True)


# ========================= Orquestación de scripts =========================
def _stream_process(proc: subprocess.Popen, name: str):
	"""Reenvía stdout/stderr del proceso con estilos Rich en tiempo real."""
	def _pipe_to_console(pipe, style):
		for line in iter(pipe.readline, ''):
			if not line:
				break
			cprint(line.rstrip(), style)
		pipe.close()

	threads = []
	if proc.stdout is not None:
		t_out = threading.Thread(target=_pipe_to_console, args=(proc.stdout, "info"), daemon=True)
		threads.append(t_out)
		t_out.start()
	if proc.stderr is not None:
		t_err = threading.Thread(target=_pipe_to_console, args=(proc.stderr, "err"), daemon=True)
		threads.append(t_err)
		t_err.start()
	for t in threads:
		t.join()


def run_python_script(name: str, script_path: Path, passthrough: bool = False, cwd: Path | None = None, as_module: str | None = None) -> None:
	repo_root = Path(__file__).resolve().parent
	script_path = script_path if script_path.is_absolute() else (repo_root / script_path)
	if not script_path.exists():
		raise FileNotFoundError(f"No se encontró el script: {script_path}")

	_panel(f"Ejecutando: {name}", str(script_path), style="title")

	env = os.environ.copy()
	env.setdefault("MPLBACKEND", "Agg")
	env.setdefault("PYTHONUNBUFFERED", "1")

	if passthrough:
		# Salida directa al terminal (útil para scripts interactivos como Req2)
		cmd = [sys.executable]
		if as_module:
			cmd += ["-m", as_module]
		else:
			cmd += [str(script_path)]
		result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env)
		if result.returncode != 0:
			_panel(f"[{name}] Falló", f"Código de salida: {result.returncode}", style="err")
			raise SystemExit(result.returncode)
		_panel(f"[{name}] Completado", "Ejecución finalizada correctamente.", style="ok")
		return

	# Modo con streaming estilizado
	cmd = [sys.executable]
	if as_module:
		cmd += ["-m", as_module]
	else:
		cmd += [str(script_path)]
	proc = subprocess.Popen(
		cmd,
		cwd=str(cwd) if cwd else None,
		env=env,
		stdin=sys.stdin,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		text=True,
		bufsize=1,
	)
	_stream_process(proc, name)
	proc.wait()
	if proc.returncode != 0:
		_panel(f"[{name}] Falló", f"Código de salida: {proc.returncode}", style="err")
		raise SystemExit(proc.returncode)
	_panel(f"[{name}] Completado", "Ejecución finalizada correctamente.", style="ok")


def _list_new_files(folder: Path, since_ts: float) -> list[tuple[str, int]]:
	items: list[tuple[str, int]] = []
	if not folder.exists():
		return items
	for p in folder.rglob('*'):
		if p.is_file():
			try:
				if p.stat().st_mtime >= since_ts:
					items.append((str(p.relative_to(Path(__file__).resolve().parent)), p.stat().st_size))
			except Exception:
				pass
	# Ordenar por nombre
	items.sort(key=lambda x: x[0])
	return items


def main():
	# Encabezado
	cprint("\n╔════════════════════════════════════════════════════════════╗", "title")
	cprint("  ORQUESTADOR DEL PROYECTO BIBLIOMETRÍA", "title")
	cprint("╚════════════════════════════════════════════════════════════╝\n", "title")

	check_and_setup_env()

	# Mostrar mensajes y solicitar credenciales al inicio (sin cambiar cómo otros módulos las leen)
	_show_intro_messages()
	_ensure_env_with_credentials()

	if hay_bibtex_validos(CARPETA_DATA):
		_panel("Optimización", "Se detectaron archivos BibTeX válidos en 'data/'. Se omite el scraping.", style="warn")
	else:
		_panel("Scraping", "Iniciando scraping automatizado y guardado en carpeta 'data'", style="info")
		ejecutar_scraping()
		_panel("Scraping", "Proceso de scraping finalizado", style="ok")

	# Unificar archivos independientemente de si se scrapeó o no
	cprint("\n📦 Unificando archivos...", "info")
	try:
		salida = unificar()
		# Mostrar pequeño resumen
		data_dir = Path(CARPETA_DATA)
		total_archivos = len([p for p in data_dir.iterdir() if p.is_file()]) if data_dir.exists() else 0
		_table(
			"Unificación completada",
			["Carpeta origen", "Archivos", "Salida"],
			[[str(data_dir), total_archivos, str(Path(salida).relative_to(Path(__file__).resolve().parent))]],
		)
	except Exception as e:
		_panel("Unificación falló", str(e), style="err")
		raise

	# ============== Secuencia de ejecución requerida ==============
	repo_root = Path(__file__).resolve().parent

	# 1) mainGrafos
	run_python_script(
		name="Grafos (citaciones, SCC y coocurrencia)",
		script_path=repo_root / "Scripts grafo" / "mainGrafos.py",
		passthrough=False,
	)

	# 2) mainReq2 (interactivo). Dejamos que el script gestione su propio UI Rich.
	#    Además, al terminar listamos outputs nuevos en algoritmosReq2/data_req2
	req2_data_dir = repo_root / "algoritmosReq2" / "data_req2"
	since = time.time()
	run_python_script(
		name="Algoritmos de similitud (Req2)",
		script_path=repo_root / "algoritmosReq2" / "mainReq2.py",
		passthrough=True,
		as_module="algoritmosReq2.mainReq2",
	)
	nuevos_req2 = _list_new_files(req2_data_dir, since)
	if nuevos_req2:
		_table(
			"Archivos generados (Req2)",
			["Ruta", "Tamaño (bytes)"],
			[[p, s] for p, s in nuevos_req2],
		)

	# 3) mainReq3_4
	since = time.time()
	run_python_script(
		name="Frecuencia y clustering de abstracts (Req3-4)",
		script_path=repo_root / "Requerimiento3-4" / "mainReq3_4.py",
		passthrough=False,
	)
	req34_out = repo_root / "Requerimiento3-4" / "data_graficos"
	nuevos_r34 = _list_new_files(req34_out, since)
	if nuevos_r34:
		_table(
			"Gráficos generados (Req3-4)",
			["Ruta", "Tamaño (bytes)"],
			[[p, s] for p, s in nuevos_r34],
		)

	# 4) mainReq5
	run_python_script(
		name="Mapas de calor y reportes (Req5)",
		script_path=repo_root / "requerimiento5" / "mainReq5.py",
		passthrough=False,
	)

	_panel("Pipeline completado", "Todos los componentes fueron ejecutados en secuencia.", style="ok")


if __name__ == "__main__":
	main()
	# Si deseas correr posteriormente análisis de similitud, ajusta la ruta adecuada
	# file_path = "data/unified_articles.csv"
	# run_similarity_analysis(file_path)

















