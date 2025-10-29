import os
import sys
import runpy
import traceback


def run_script(script_path: str, title: str) -> None:
	"""
	Ejecuta un script Python en el mismo intérprete, de forma secuencial.
	- script_path: ruta absoluta del archivo .py a ejecutar
	- title: nombre descriptivo para logs
	Lanza excepción si el script falla.
	"""
	print(f"\n=== Ejecutando: {title} ===")
	print(f"Ruta: {script_path}")
	if not os.path.isfile(script_path):
		raise FileNotFoundError(f"No se encontró el script: {script_path}")

	# Ejecutar como si fuera __main__ para respetar código al nivel del módulo
	runpy.run_path(script_path, run_name="__main__")
	print(f"=== Finalizado: {title} ===\n")


def main() -> int:
	# Directorio actual (donde está este archivo)
	base_dir = os.path.dirname(__file__)

	# Asegurar backend no interactivo para matplotlib (evita problemas en entornos sin display)
	try:
		import matplotlib
		matplotlib.use("Agg", force=True)
	except Exception:
		# Si fallara, continuamos (los scripts también guardan a archivo)
		pass

	# Rutas de los scripts a ejecutar en orden
	scripts = [
		(os.path.join(base_dir, "clustering_abstracts.py"), "1) clustering_abstracts"),
		(os.path.join(base_dir, "analisis_frecuencia_abstracts.py"), "2) analisis_frecuencia_abstracts"),
	]

	# Validar que el archivo de entrada exista para ambos scripts
	productos_path = os.path.join(os.path.dirname(base_dir), "productosUnificados", "productosUnificados.txt")
	if not os.path.exists(productos_path):
		print(
			f"ERROR: No se encontró el archivo requerido: {productos_path}\n"
			"Verifica que la ruta y el nombre del archivo sean correctos."
		)
		return 1

	# Ejecutar secuencialmente
	try:
		for path, title in scripts:
			run_script(path, title)
	except SystemExit as e:
		# Si alguno de los scripts llama a exit(), capturar y convertir a error controlado
		code = int(e.code) if isinstance(e.code, int) else 1
		print(f"\nEl script terminó con SystemExit(code={code}).")
		return code
	except Exception:
		print("\nSe produjo una excepción durante la ejecución de los scripts:\n")
		traceback.print_exc()
		return 1

	print("Secuencia completada correctamente.\n")
	# Mostrar dónde quedan los outputs principales
	data_graficos = os.path.join(base_dir, "data_graficos")
	print(f"Gráficos esperados en: {data_graficos}")
	return 0


if __name__ == "__main__":
	sys.exit(main())

