# OpenWM

**Open-source Warehouse Management System — a Docker-native demo platform for showcasing modern WMS capabilities.**

OpenWM packages the four core warehouse-management workflows into a single `docker compose up`:

- **Inventory** — products, locations, stock-on-hand, full movement audit trail
- **Inbound** — purchase orders, receiving, put-away
- **Outbound** — sales orders, picking, packing, shipping
- **Reporting** — live KPI dashboard, throughput charts, low-stock alerts

Each module is a self-contained slice (its own models, services, API routes, and React feature folder), so the architecture itself reads as professional during technical conversations.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Once startup completes (2–5 minutes on first run):

| Service       | URL                          | Notes                                          |
|---------------|------------------------------|------------------------------------------------|
| Web UI        | http://localhost:5173        | The demo surface                                |
| API docs      | http://localhost:8000/docs   | Swagger — useful for technical demos            |
| pgAdmin       | http://localhost:5050        | Login: `admin@openwm.local` / `admin`          |

The API container automatically runs database migrations and seeds **50 products, 29 locations, 10 purchase orders, and 20 sales orders** with realistic history, so the dashboard looks alive on first open.

## Demo walkthrough (~3 minutes)

A scripted path that touches every module — perfect for an intro call:

1. **Open the dashboard** at http://localhost:5173. Point out the four KPI cards, the 14-day throughput chart, and the stock-by-zone bar chart. Mention the dashboard auto-refreshes every 15 seconds.
2. **Inventory → Stock** — show the live stock-on-hand grid. Filter to one zone. Note the lot numbers and per-location quantities.
3. **Inbound** — open an open purchase order. Click **Receive**, accept the pre-filled quantities, and confirm. Stock appears immediately in the Inventory view.
4. **Outbound** — open a sales order. Click **Pick & ship**. The system pre-fills picks from the locations with the most stock; show that the operator can override location, quantity, or split picks. Confirm.
5. **Inventory → Movements** — show the ledger entries created by the two transactions above (`RECEIPT` and `PICK` with back-references to the source document).
6. **Back to the dashboard** — within 15 seconds the throughput chart, top-movers list, and recent-activity feed reflect the new transactions.

## Documentation

- [Functional overview](docs/functional/overview.md) — what the system does (business view)
- [Inventory module](docs/functional/inventory.md)
- [Inbound module](docs/functional/inbound.md)
- [Outbound module](docs/functional/outbound.md)
- [Reporting module](docs/functional/reporting.md)
- [Deployment manual](docs/deployment/deployment-manual.md) — how to install and run it
- [Configuration reference](docs/deployment/configuration.md)
- [Upgrading](docs/deployment/upgrading.md)
- [Troubleshooting](docs/deployment/troubleshooting.md)

## Tech stack

| Layer    | Choice                                                            |
|----------|-------------------------------------------------------------------|
| Backend  | Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2        |
| Database | PostgreSQL 16                                                     |
| Frontend | React 18 + Vite + TypeScript, TailwindCSS, shadcn/ui, TanStack Query, Recharts |
| Infra    | Docker + Docker Compose (`db` · `api` · `web` · `pgadmin`)         |

## Project layout

```
OpenWM/
├── docker-compose.yml
├── .env.example
├── docs/                   functional + deployment docs
├── backend/
│   └── app/
│       ├── core/           config, db session, deps
│       ├── modules/        one folder per WMS domain
│       │   ├── inventory/  models, schemas, service, router
│       │   ├── inbound/
│       │   ├── outbound/
│       │   └── reporting/
│       └── seed/           demo data loader
└── frontend/
    └── src/
        ├── components/ui/  shadcn primitives
        ├── lib/            api client, utils
        └── features/       one folder per WMS domain
            ├── inventory/
            ├── inbound/
            ├── outbound/
            └── reporting/
```

**Module discipline rule:** each backend module owns its own `models.py`, `schemas.py`, `service.py`, `router.py`. Cross-module access goes through service functions, never direct ORM imports.

## Status

This codebase is **demo-grade**, not production-grade. Before exposing it to anything beyond a controlled demo environment, work through the production hardening checklist in the [deployment manual](docs/deployment/deployment-manual.md#6-production-hardening-checklist).
