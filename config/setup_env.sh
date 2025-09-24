#!/bin/bash
# filepath: config/setup_env.sh

echo "Creando entorno virtual..."
python3 -m venv venv

echo "Activando entorno virtual..."
source venv/bin/activate

echo "Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Entorno virtual configurado correctamente."
