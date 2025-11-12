#!/usr/bin/env bash


set -e


# Crear entorno si no existe
echo "[INFO] Verificando entorno virtual..."
uv venv


# Instalar dependencias si faltan
echo "[INFO] Instalando dependencias..."
uv sync


# Inicializar base de datos de caché
mkdir -p data
touch data/cache.db


# Ejecutar servidor FastAPI
uv run uvicorn orchestrator:app --reload --host 0.0.0.0 --port 8000