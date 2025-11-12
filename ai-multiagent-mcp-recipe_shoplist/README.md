# MCP Multi-agent - Demo

1. Crear un virtualenv e instalar dependencias:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Poner variables de entorno (opcional):

```
export SPOONACULAR_KEY=...
export SERPAPI_KEY=...
export CACHE_DB=./data/cache.db
```

3. Ejecutar demo:

```
./run.sh
# o
python -m uvicorn orchestrator:app --reload
```

4. POST a `http://localhost:8000/process-recipe` con JSON: `{ "recipe_url": "https://..." }`
```

---

## Comentarios finales

- Todo el IO es asíncrono (httpx + aiosqlite) para evitar operaciones bloqueantes.
- Se usa `aiosqlite` (SQLite) por portabilidad. Si quieres, cambio a Redis para mayor rendimiento y concurrencia.
- He activado la preferencia por `uvloop` en el script de arranque, pero `uvicorn` ya usa uvloop internamente si está instalado.

Si quieres que genere un ZIP del repo, o que cree el repo en GitHub/Gist, lo hago ahora. También puedo cambiar la DB a Redis (con `aioredis`) si prefieres.