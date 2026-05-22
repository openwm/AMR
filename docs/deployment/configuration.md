# Configuration Reference

All configuration is via environment variables in the `.env` file at the project root. `cp .env.example .env` to start. The defaults are appropriate for a local demo; the **Production note** column flags variables you must change before any non-local deployment.

## Environment variables

| Variable                  | Default                              | Description                                                | Production note               |
|---------------------------|--------------------------------------|------------------------------------------------------------|-------------------------------|
| `POSTGRES_DB`             | `openwm`                             | Database name                                              |                               |
| `POSTGRES_USER`           | `openwm`                             | Database user                                              | Use a stronger username       |
| `POSTGRES_PASSWORD`       | `openwm_dev`                         | Database password                                          | **Change**                    |
| `POSTGRES_PORT`           | `5432`                               | Host port for postgres                                     |                               |
| `API_PORT`                | `8000`                               | Host port for the FastAPI service                          |                               |
| `JWT_SECRET`              | `change-me-in-production`            | Signing key for JWTs                                       | **Change** (`openssl rand -hex 32`) |
| `JWT_ALGORITHM`           | `HS256`                              | JWT algorithm                                              |                               |
| `JWT_EXPIRES_MINUTES`     | `480`                                | Token lifetime                                             | Lower for production          |
| `SEED_DEMO_DATA`          | `true`                               | If true, populate demo data on first start                 | **Set to `false`**            |
| `CORS_ORIGINS`            | `http://localhost:5173`              | Comma-separated allow-list of frontend origins              | Restrict to actual origin     |
| `WEB_PORT`                | `5173`                               | Host port for the React dev server                         |                               |
| `VITE_API_URL`            | `http://localhost:8000`              | API URL the frontend talks to                              | Set to public API origin      |
| `PGADMIN_EMAIL`           | `admin@openwm.local`                 | pgAdmin login email                                        | **Change** or remove pgAdmin  |
| `PGADMIN_PASSWORD`        | `admin`                              | pgAdmin login password                                     | **Change** or remove pgAdmin  |
| `PGADMIN_PORT`            | `5050`                               | Host port for pgAdmin                                      |                               |

## Exposed ports

| Container        | Host port      | Container port | Purpose                          |
|------------------|----------------|----------------|----------------------------------|
| `openwm-db`      | `${POSTGRES_PORT}` (5432) | 5432   | PostgreSQL — open for pgAdmin / DB tools |
| `openwm-api`     | `${API_PORT}` (8000)      | 8000   | FastAPI HTTP + Swagger UI         |
| `openwm-web`     | `${WEB_PORT}` (5173)      | 5173   | React Vite dev server             |
| `openwm-pgadmin` | `${PGADMIN_PORT}` (5050)  | 80     | pgAdmin web UI                    |

If a port collides on your host, change only the host-side value (the left of the colon) in `.env`; container ports are fixed.

## Named volumes

| Volume          | Used by   | Purpose                                                              |
|-----------------|-----------|----------------------------------------------------------------------|
| `pgdata`        | `db`      | PostgreSQL data directory — **back up this volume**                  |
| `pgadmin_data`  | `pgadmin` | pgAdmin's connection registrations and preferences                   |

Inspect volumes with:

```bash
docker volume ls
docker volume inspect openwm_pgdata
```

## Bind mounts

For development convenience, `./backend` and `./frontend` are bind-mounted into the `api` and `web` containers respectively. This enables hot reload — edits on your host are reflected immediately. For production, remove these bind mounts and build the code into immutable images.
