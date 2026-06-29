# Local Docker Deployment

This guide runs Keneya Lab locally with Docker Compose for a clinic/lab machine or a local network server.

## Requirements

- Docker Engine or Docker Desktop with Docker Compose v2.
- Ports `80`, `8000`, `5173`, `5432`, `8080`, and `9000` available, depending on which services you expose.
- A configured `.env` file at the repository root.

If another local service is already using HTTP or Postgres, stop it first:

```bash
sudo systemctl stop apache2
sudo systemctl stop postgresql
```

## Configure `.env`

For local Docker, keep these values or adapt them carefully:

```env
DOMAIN=localhost
FRONTEND_HOST=http://localhost:5173
ENVIRONMENT=local

POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_DB=app
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change-this-local-password

MINIO_ENDPOINT=minio:9000
MINIO_PUBLIC_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=keneyalab
MINIO_SECRET_KEY=change-this-local-minio-secret
MINIO_BUCKET=keneyalab-results
MINIO_SECURE=False
```

Also change these from defaults before real local use:

```env
SECRET_KEY=generate-a-long-random-secret
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=change-this-admin-password
```

Generate a secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Start The Stack

From the repository root:

```bash
docker compose up -d --build
```

This uses `compose.yml` plus `compose.override.yml` automatically. The local override exposes useful ports and runs the backend with reload.

Check status:

```bash
docker compose ps
docker compose logs -f backend
```

## Access URLs

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Adminer: `http://localhost:8080`
- MinIO API: `http://localhost:9000`

Login with `FIRST_SUPERUSER` and `FIRST_SUPERUSER_PASSWORD` from `.env`.

## Email

Mailcatcher is for development only. For a local deployment used by a lab, configure a real SMTP relay in `.env`:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_TLS=True
SMTP_SSL=False
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
EMAILS_FROM_EMAIL=noreply@example.com
EMAILS_FROM_NAME="Keneya Lab"
```

If the local deployment will not send email, leave `SMTP_HOST` and `EMAILS_FROM_EMAIL` empty.

## Persistent Data

Clinical data is stored in Docker named volumes:

- `app-db-data`: PostgreSQL database.
- `app-minio-data`: uploaded lab logos and result images.

Verify:

```bash
docker compose config --volumes
docker volume ls | grep keneyalab
```

Do not run this unless you intentionally want to delete all local data:

```bash
docker compose down -v
```

Use this for normal restarts while preserving data:

```bash
docker compose down
docker compose up -d
```

## Initial Data And Demo Data

Initialize users/RBAC if needed:

```bash
docker compose exec backend python -c "from app.core.db import init_db; from app.core.db import engine; from sqlmodel import Session; session = Session(engine); init_db(session)"
```

Seed the demo catalog:

```bash
docker compose exec backend python -m app.seed_catalog_demo --confirm-delete
```

Seed one all-in-one demo order with normal, abnormal, and critical results:

```bash
docker compose exec backend python -m app.seed_demo_order_results
```

Clear business data while preserving users and RBAC:

```bash
docker compose exec backend python scripts/clear_data.py
```

## Backup And Restore

Backup the database:

```bash
docker compose exec db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > keneyalab-db.sql
```

Restore the database:

```bash
cat keneyalab-db.sql | docker compose exec -T db psql -U "$POSTGRES_USER" "$POSTGRES_DB"
```

Back up MinIO uploads by copying the Docker volume data or using the MinIO client. At minimum, keep a host/server backup of the `app-minio-data` Docker volume together with the database backup.

## Update The App

After pulling code changes:

```bash
docker compose up -d --build backend frontend prestart
```

If dependencies or generated assets changed, rebuild all services:

```bash
docker compose up -d --build --force-recreate backend frontend prestart
```

## Troubleshooting

If services do not start:

```bash
docker compose ps
docker compose logs backend
docker compose logs db
docker compose logs minio
```

If Postgres is unhealthy, confirm `.env` has matching `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`.

If uploads or report logos fail, confirm MinIO is running and the bucket exists:

```bash
docker compose ps minio minio-init
docker compose logs minio-init
```

If local ports are already in use, stop the conflicting host service or change the port mapping in `compose.override.yml`.
