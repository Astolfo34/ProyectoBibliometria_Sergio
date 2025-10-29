from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path


def run_step(python_exec: Path, script_path: Path, name: str) -> None:
	print(f"\n=== [{name}] Iniciando ===")
	env = os.environ.copy()
	# Evitar bloqueos de GUI de matplotlib en entornos sin display
	env.setdefault("MPLBACKEND", "Agg")
	try:
		subprocess.run([str(python_exec), str(script_path)], check=True, env=env)
		print(f"=== [{name}] Completado ===\n")
	except subprocess.CalledProcessError as e:
		print(f"*** [{name}] Falló con código {e.returncode}. Abortando pipeline. ***")
		raise SystemExit(e.returncode)


def main() -> int:
	# Raíz del proyecto (.. desde este archivo): ws_analisisBibliometrico/
	project_root = Path(__file__).resolve().parents[1]

	# Intérprete Python: preferir el mismo que ejecuta este script
	python_exec = Path(sys.executable)

	# Rutas de scripts a ejecutar en orden
	mapa_calor_dir = project_root / "requerimiento5" / "mapaCalor"
	steps = [
		("normalizar_data", mapa_calor_dir / "normalizar_data.py"),
		# El archivo real es 'generaMapaCalor.py'
		("generarMapaCalor", mapa_calor_dir / "generaMapaCalor.py"),
		("nubePalabras", mapa_calor_dir / "nubePalabras.py"),
		("generar_lineaTemporal", mapa_calor_dir / "generar_lineaTemporal.py"),
		("generar_informesPDF", mapa_calor_dir / "generar_informesPDF.py"),
	]

	# Validar existencia de scripts
	missing = [name for name, path in steps if not path.exists()]
	if missing:
		print(f"No se encontraron los siguientes scripts: {', '.join(missing)}")
		return 1

	# Ejecutar secuencialmente
	for name, path in steps:
		run_step(python_exec, path, name)

	print("Pipeline finalizado correctamente.")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

