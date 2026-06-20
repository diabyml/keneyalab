# Development Workflows

## Clear db except rbac system
docker compose exec backend python scripts/clear_data.py

## To access adminer: http://adminer.localhost/

## Mailcatcher  http://localhost:1080


## run permissions seed
docker compose exec backend python -c "from app.core.db import init_db; from app.core.db import engine; from sqlmodel import Session; session = Session(engine); init_db(session)"



## seed catalog demo
docker compose exec backend python -m app.seed_catalog_demo  --confirm-delete

## Fresh build backend and Frontend
```bash
docker compose build  backend frontend && docker compose up -d backend frontend

```

## Regenerate Frontend API Client

The frontend client SDK (`frontend/src/client/sdk.gen.ts`) is auto-generated from the backend's OpenAPI schema. Regenerate it whenever you change the backend API (new endpoints, changed models, removed endpoints).

### Steps

```bash
# 1. Make sure the backend is running
cd backend && uv run uvicorn app.main:app --port 8000

# 2. Fetch the OpenAPI schema
curl http://localhost:8000/api/v1/openapi.json > frontend/openapi.json

# 3. Generate the client SDK
cd frontend && bun run generate-client
```

### When to run this

- After adding, removing, or renaming an API endpoint
- After changing request/response models on any endpoint
- After adding or removing query parameters
- If the frontend build fails with missing types from `@/client`

### What gets generated

| Output | Description |
|---|---|
| `frontend/src/client/sdk.gen.ts` | Typed service classes and request functions |
| `frontend/src/client/types.gen.ts` | Request/response TypeScript types |
| `frontend/src/client/schemas.gen.ts` | JSON Schema definitions |

### How it works

1. Backend serves live OpenAPI spec at `/api/v1/openapi.json`
2. `curl` saves it to `frontend/openapi.json`
3. `bun run generate-client` runs `@hey-api/openapi-ts` (configured in `frontend/openapi-ts.config.ts`)
4. The generator reads `frontend/openapi.json` and writes the client SDK

## Rebuild Docker Containers

After backend/frontend code changes, rebuild and restart:

```bash
docker compose up -d --build backend frontend prestart
```

## Architecture

The backend follows a strict 3-layer architecture:

```
API (routes) → Services (business logic) → Repositories (DB access)
```

- **Routes**: thin, validate input, call service, return response. No business logic.
- **Services**: own transactions (`commit`/`rollback`), orchestrate workflows, raise domain exceptions.
- **Repositories**: pure DB access. Never commit, never create sessions. `create()` uses `flush()` to populate DB-generated fields.
