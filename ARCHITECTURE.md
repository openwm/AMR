# OpenWM

**Open-source multi-system warehouse platform — a Docker-native demo for showcasing modern WMS/WCS capabilities.**

OpenWM runs as a single `docker compose up` and currently ships two active systems:

- **WMS** — Warehouse Management System (inventory, inbound, outbound, planning, reporting)
- **WCS** — Warehouse Control System (station queue manager, AMR dispatch, pace tracking)

Two further systems — **Equipment** and **Devices** — are scaffolded and ready for implementation.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Once startup completes (2–5 minutes on first run):

| Service    | URL                        | Notes                                       |
|------------|----------------------------|---------------------------------------------|
| Web UI     | http://localhost:5173      | Single-page app; WMS + WCS in one sidebar   |
| API docs   | http://localhost:8000/docs | Swagger — all WMS and WCS endpoints         |
| pgAdmin    | http://localhost:5050      | Login: `admin@openwm.dev` / `admin`         |

The API container automatically runs database migrations and seeds **50 products, 27 locations, 10 purchase orders, and 20 sales orders** with realistic history so the dashboard looks alive on first open.

## Tech stack

| Layer     | Choice                                                                          |
|-----------|---------------------------------------------------------------------------------|
| Backend   | Python 3.12 · FastAPI · SQLAlchemy 2.x · Alembic · Pydantic v2 · httpx         |
| Databases | PostgreSQL 16 (relational state) · Redis 7 (WCS queue & pace state)             |
| Frontend  | React 18 · Vite · TypeScript · TailwindCSS · shadcn/ui · TanStack Query · Recharts |
| Infra     | Docker Compose — `db` · `redis` · `api` · `web` · `pgadmin`                    |

## Systems

### WMS — Warehouse Management System

Five self-contained modules, each owning `models.py · schemas.py · service.py · router.py`:

| Module    | API prefix            | Responsibility                                      |
|-----------|-----------------------|-----------------------------------------------------|
| inventory | `/api/wms/inventory`  | Products, locations, stock-on-hand, movement ledger |
| inbound   | `/api/wms/inbound`    | Purchase orders, receipts, put-away                 |
| outbound  | `/api/wms/outbound`   | Sales orders, shipments, pick/ship                  |
| planning  | `/api/wms/planning`   | Order allocation against available stock            |
| reporting | `/api/wms/reporting`  | KPI dashboard, throughput, top movers, low-stock    |

Cross-module access goes through service functions only — never direct ORM imports across module boundaries.

### WCS — Warehouse Control System

Stateless API backed entirely by Redis. No SQL tables.

| Endpoint                                         | What it does                                                                         |
|--------------------------------------------------|--------------------------------------------------------------------------------------|
| `POST /api/wcs/tasks`                            | Creates a `PickTask`, scores priority by order deadline, assigns to the station with the lowest queue depth (max 5) and lowest inflight AMR count (max 3) |
| `GET  /api/wcs/stations`                         | Lists all stations with queue depth, AMR count, rolling picks/hr                     |
| `GET  /api/wcs/stations/:id/queue`               | Returns `at_dock` tasks (priority order) then `queued` tasks                         |
| `POST /api/wcs/stations/:id/tasks/:id/advance`   | Moves a task `at_dock → picking`; promotes next queued task to `at_dock`             |
| `POST /api/wcs/stations/:id/tasks/:id/complete`  | Marks complete, records pace tick, fires `PATCH` to WMS API, triggers refill if queue depth < 3 |
| `POST /api/wcs/stations/:id/tasks/:id/exception` | Sidelines task, advances next `at_dock` task into the active picking slot            |

**Task state machine:**
```
queued ──(auto-promote)──► at_dock ──(advance)──► picking ──(complete)──► completed
                                └──(exception)──────────────────────────► exception
```

**Redis key schema** (`decode_responses=True`, all values strings):

| Key | Type | Purpose |
|-----|------|---------|
| `wcs:stations` | SET | Registry of station IDs |
| `wcs:station:{id}:queue` | ZSET (score = deadline epoch) | Priority queue of `queued` tasks |
| `wcs:station:{id}:at_dock` | ZSET (score = deadline epoch) | Tasks docked and awaiting picker |
| `wcs:station:{id}:amr_count` | STRING int | Inflight AMR count |
| `wcs:station:{id}:picks` | ZSET (score = unix timestamp) | Pick timestamps for rolling 60-min pace; trimmed to 2-hour window |
| `wcs:task:{id}` | HASH | Full task payload |

Three stations are seeded on API startup: `STA-01`, `STA-02`, `STA-03`.

## Project layout

```
OpenWM/
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── functional/         business-level module docs
│   └── deployment/         install, config, upgrade, troubleshoot
├── backend/
│   ├── requirements.txt
│   ├── alembic/            migration versions (WMS only; WCS uses Redis)
│   └── app/
│       ├── core/           config, db session, dependency injection
│       ├── systems/
│       │   ├── wms/        WMS modules (inventory · inbound · outbound · planning · reporting)
│       │   │   └── {module}/   models.py · schemas.py · service.py · router.py
│       │   ├── wcs/        WCS (Redis-backed; no SQLAlchemy models)
│       │   │   ├── redis_client.py
│       │   │   ├── schemas.py
│       │   │   ├── service.py
│       │   │   └── router.py
│       │   ├── equipment/  stub
│       │   └── devices/    stub
│       └── seed/           demo data loader (WMS only)
└── frontend/
    └── src/
        ├── components/ui/  shadcn/ui primitives
        ├── lib/            axios client, cn utility
        └── systems/
            ├── wms/        one feature folder per WMS module
            │   └── {module}/   api.ts · types.ts · index.tsx · *Page.tsx
            ├── wcs/        StationQueueManager (live-polling, action buttons)
            ├── equipment/  stub
            └── devices/    stub
```

## API routing conventions

```
/api/wms/{module}/...   WMS endpoints (PostgreSQL-backed)
/api/wcs/...            WCS endpoints (Redis-backed)
```

All routes are registered in `backend/app/main.py`. The `lifespan` handler seeds WCS station keys into Redis on startup.

## Frontend navigation

A single sidebar app. WMS modules and the WCS Station Queue are grouped under labelled sections separated by a divider. The URL space is flat within each system:

```
/                   WMS dashboard
/inventory/*        WMS inventory
/inbound/*          WMS inbound
/outbound/*         WMS outbound
/planning           WMS planning
/wcs/stations       WCS station queue manager
```

TanStack Query polls the station list every 5 s and individual queues every 3 s so the UI reflects state changes without manual refresh.

## Status

This codebase is **demo-grade**, not production-grade. Before exposing it beyond a controlled demo environment, work through the production hardening checklist in the [deployment manual](docs/deployment/deployment-manual.md#6-production-hardening-checklist).
