# Deployment Manual

This manual is the single source of truth for installing, running, and operating OpenWM. If anything here is unclear or wrong, that is a bug — please file an issue.

## 1. Prerequisites

| Requirement      | Minimum            | Notes                                                       |
|------------------|--------------------|-------------------------------------------------------------|
| Docker Engine    | 24.x or newer      | On Windows / macOS, install **Docker Desktop** (≥ 4.30)     |
| Docker Compose   | v2 (built-in)      | Bundled with Docker Desktop and recent Docker Engine        |
| Disk space       | ~2 GB              | For images + Postgres data volume                           |
| RAM              | 2 GB free          | All four containers running                                 |
| Free ports       | 5173, 8000, 5432, 5050 | Configurable via `.env`                                  |

Verify Docker is installed:

```bash
docker --version
docker compose version
```

## 2. Install & first run

```bash
# 1. Clone the repository
git clone <your-repo-url> openwm
cd openwm

# 2. Configure environment (the defaults are fine for a demo)
cp .env.example .env

# 3. Build and start everything
docker compose up --build
```

The first run takes **2–5 minutes** while images download and dependencies install. Subsequent starts complete in seconds.

When startup completes, the API container will:

1. Wait for PostgreSQL to be healthy
2. Run all Alembic migrations (`alembic upgrade head`)
3. Run the demo seeder (`python -m app.seed.seed`) — populates ~50 products, 29 locations, 10 purchase orders (with receipts) and 20 sales orders (most shipped). Skipped if the catalog is already populated.
4. Start the FastAPI server with hot reload

## 3. Service endpoints

Once the stack is up:

| Service      | URL                                | Default credentials                        |
|--------------|------------------------------------|--------------------------------------------|
| Web UI       | http://localhost:5173              | (auth not yet enabled in this demo build)  |
| API root     | http://localhost:8000              |                                            |
| API docs     | http://localhost:8000/docs         | Swagger UI — try any endpoint              |
| API health   | http://localhost:8000/health       | Returns `{"status":"ok"}`                  |
| pgAdmin      | http://localhost:5050              | `admin@openwm.local` / `admin`             |
| PostgreSQL   | localhost:5432                     | `openwm` / `openwm_dev`                    |

## 4. Walking the demo path

After the seeder runs, you have realistic data. To **show the end-to-end flow live**:

1. Open the dashboard — KPI cards and charts should show populated data
2. Go to **Inventory → Products** — show the catalog (search, create new product)
3. Go to **Inbound** — show open POs, open one, click **Receive** to receive the remaining quantity
4. Go back to **Inventory → Stock** — the just-received stock now appears
5. Go to **Outbound** — open an open SO, click **Pick & ship**, confirm
6. Go to **Inventory → Movements** — show the audit trail with the new entries
7. Return to **Dashboard** — refreshes within 15 seconds and shows updated throughput

## 5. Operating the stack

### Starting / stopping

```bash
docker compose up -d              # start in background
docker compose down               # stop containers (keeps data)
docker compose down -v            # stop AND delete the database volume
```

### Logs

```bash
docker compose logs -f api        # follow API logs
docker compose logs -f db         # follow database logs
docker compose logs -f web        # follow frontend logs
```

### Resetting demo data

```bash
docker compose down -v            # wipe the postgres volume
docker compose up --build         # fresh start, seeds again
```

### Disabling the seeder

Set `SEED_DEMO_DATA=false` in `.env` before first start. Useful if you want to demo against an empty system.

## 6. Production hardening checklist

This codebase is **demo-grade**, not production-grade. Before exposing it beyond a controlled demo environment:

- [ ] **Change `JWT_SECRET`** in `.env` to a long random value (`openssl rand -hex 32`)
- [ ] **Change `POSTGRES_PASSWORD`** and database user
- [ ] **Change pgAdmin credentials** or remove the pgAdmin service from `docker-compose.yml`
- [ ] **Set `SEED_DEMO_DATA=false`** to prevent demo data being inserted in real environments
- [ ] **Disable hot reload** by building a production image (replace `--reload` in the Dockerfile CMD and serve the frontend via `npm run build` + a static server like nginx)
- [ ] **Put the API behind a reverse proxy** (Caddy, nginx, Traefik) terminating TLS
- [ ] **Lock down `CORS_ORIGINS`** to your actual frontend origin
- [ ] **Back up the `pgdata` volume** on a schedule (see § 7)
- [ ] **Pin image tags** to specific versions instead of `latest`

## 7. Backup & restore

### Backup

```bash
docker exec openwm-db pg_dump -U openwm -d openwm -F c -f /tmp/openwm.dump
docker cp openwm-db:/tmp/openwm.dump ./openwm-$(date +%Y%m%d).dump
```

### Restore (into a fresh stack)

```bash
docker compose up -d db
docker cp ./openwm-20260522.dump openwm-db:/tmp/openwm.dump
docker exec openwm-db pg_restore -U openwm -d openwm --clean --if-exists /tmp/openwm.dump
docker compose up -d api web
```

## 8. Where to go next

- [Configuration reference](configuration.md) — every env var, port, and volume
- [Upgrading](upgrading.md) — pulling a new version
- [Troubleshooting](troubleshooting.md) — known failure modes and fixes
