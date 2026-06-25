# Warehouse Management System

## Overview
REST API-only system (no message brokers). Four modules:
- **WMS** — order lifecycle, inventory, ERP sync
- **WCS** — pick task orchestration, AMR dispatch, station queue management
- **Equipment** — AMR state machines, shelf and station domain models
- **Devices** — REST adapters for AMR fleet API, barcode scanner webhooks, operator UI WebSocket

---

## Stack
- **Runtime:** Node.js 20+ (TypeScript 5)
- **Framework:** Express 4
- **Primary DB:** PostgreSQL 16 (orders, inventory, tasks, audit)
- **Cache / queue state:** Redis 7 (station queues, AMR state, operator pace)
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS
- **Testing:** Jest + Supertest (backend), Vitest + React Testing Library (frontend)
- **Package manager:** pnpm workspaces

---

## Monorepo layout

```
/warehouse-system
  /apps
    /wms-api          REST API — order lifecycle, inventory, ERP sync
    /wcs-engine       REST API — pick task orchestration, AMR dispatch
    /operator-ui      React — pick station scan UI (operator-facing, minimal)
    /dashboard-ui     React — ops/supervisor dashboard
  /packages
    /domain           Shared TypeScript interfaces, enums, state-machine helpers
    /equipment        AMR & shelf domain models, state machines (no I/O)
    /devices          HTTP adapters — AMR fleet API, barcode scanner webhooks
  /infra
    /db               PostgreSQL migrations (pg-migrate)
    /docker           docker-compose for local dev (postgres, redis)
```

---

## Module boundaries

- WMS exposes REST endpoints consumed by WCS and ERP
- WCS exposes REST endpoints consumed by the Operator UI and Equipment layer
- All inter-module calls are **HTTP only** — no shared in-process imports across app boundaries
- Shared TypeScript types live in `/packages/domain` only — apps never import from each other
- `/packages/equipment` and `/packages/devices` are imported by `wcs-engine` only

---

## Service port map (local dev)

| Service        | Port  |
|----------------|-------|
| wms-api        | 3001  |
| wcs-engine     | 3002  |
| operator-ui    | 5173  |
| dashboard-ui   | 5174  |
| PostgreSQL      | 5432  |
| Redis          | 6379  |

Configured via `.env` files per app. Never hardcode ports or URLs.

---

## Environment variables (per app)

**wms-api**
```
DATABASE_URL=postgres://...
PORT=3001
ERP_API_URL=https://erp.internal/api
ERP_API_KEY=
```

**wcs-engine**
```
DATABASE_URL=postgres://...
REDIS_URL=redis://localhost:6379
PORT=3002
WMS_API_URL=http://localhost:3001
AMR_FLEET_API_URL=https://amr.internal/api
AMR_FLEET_API_KEY=
STATION_QUEUE_MAX_DEPTH=5
STATION_INFLIGHT_AMR_MAX=3
```

**dashboard-ui / operator-ui**
```
VITE_WMS_API_URL=http://localhost:3001
VITE_WCS_API_URL=http://localhost:3002
```

---

## Authentication & authorisation

- **All backend routes** require a Bearer JWT validated by a shared middleware in `/packages/domain/auth`
- JWT issued by `wms-api` at `POST /auth/login`
- **Roles:** `operator` | `supervisor` | `admin` | `erp_service`
- **dashboard-ui** — session-based login, roles: viewer / supervisor / admin
- **operator-ui** — operator role only; auto-login by station ID + PIN
- **ERP integration** — uses `erp_service` role via API key header, not JWT

Route-level guards:
| Resource                        | Minimum role     |
|---------------------------------|------------------|
| GET  /orders                    | viewer           |
| POST /orders                    | erp_service      |
| PATCH /tasks/:id/exception      | supervisor       |
| DELETE or bulk cancel           | admin            |

---

## Database schema (key tables)

```sql
-- WMS
orders          (id, erp_ref, type, status, deadline, created_at)
order_lines     (id, order_id, sku, qty_requested, qty_picked, status)

-- WCS
pick_tasks      (id, order_line_id, station_id, amr_id, shelf_id,
                 state, priority, assigned_at, completed_at, exception_reason)
stations        (id, name, queue_max_depth, inflight_amr_max, active)

-- Equipment
amrs            (id, name, state, current_shelf_id, current_station_id, last_seen_at)
shelves         (id, location_code, current_amr_id, state)

-- Shared
audit_log       (id, entity_type, entity_id, action, actor_id, payload, created_at)
```

Redis keys:
```
station:{id}:queue          List of pick_task IDs (ordered)
station:{id}:inflight       Set of AMR IDs currently assigned
station:{id}:pace           Sorted set — pick timestamps (60-min rolling window)
amr:{id}:state              Hash — current AMR telemetry snapshot
```

---

## API conventions

- All endpoints return `{ data, error, meta }` envelope
- Errors: `{ error: { code, message, field? } }` — use HTTP status correctly
- Pagination: `?page=1&limit=20` on all list endpoints; meta includes `total`
- Timestamps: ISO 8601 UTC everywhere
- IDs: UUIDs (not integers)
- PATCH is partial update (not PUT); only send changed fields

---

## Pick task state machine

Valid transitions only — reject anything else with `409 Conflict`:

```
pending
  → amr_assigned    (WCS assigns AMR)
  → amr_en_route    (AMR departs shelf location)
  → at_dock         (AMR arrives at station — webhook)
  → picking         (operator starts scan)
  → completed       (all qty scanned and confirmed)
  → exception       (scan mismatch / short pick / AMR fault)

exception
  → completed       (supervisor resolves with actual qty)
  → cancelled       (supervisor cancels line)
  → pending         (supervisor re-queues)
```

---

## AMR state machine

```
idle → assigned → traveling → at_dock → releasing → idle
                                       ↘ faulted
faulted → idle  (supervisor releases via dashboard)
```

---

## Dashboard UI

- **App:** `/apps/dashboard-ui`
- **Stack:** React 18, TypeScript, Vite, Tailwind CSS
- **Purpose:** Internal ops tool — view orders, monitor AMR fleet,
  manage station queues, handle exceptions
- **Comms:** REST calls to WMS API and WCS engine only (no direct DB access)
- **Auth:** Session-based JWT; roles: viewer / supervisor / admin
- **Polling intervals:** Fleet 5s · Stations 3s · Orders 15s · Exceptions 10s

### Dashboard modules

| Route          | Purpose                                                    |
|----------------|------------------------------------------------------------|
| /orders        | Inbound/outbound list, status, ERP sync log, line drill-down |
| /fleet         | Live AMR grid — state colour-coded, fault resolve action   |
| /stations      | Per-station queue depth, active task, operator pace card   |
| /exceptions    | Sidelined tasks grouped by reason, resolve / reassign / cancel actions |
| /inventory     | Shelf locations, SKU stock levels                          |

---

## Operator UI

- **App:** `/apps/operator-ui`
- **Stack:** React 18, TypeScript, Vite, Tailwind CSS
- **Purpose:** Minimal, hands-free pick station screen
- **Auth:** Station ID + operator PIN (operator role)
- **Comms:** WCS engine only
- **Flow:** Task pushed via polling (`GET /stations/:id/queue`) →
  operator scans barcode → `POST /stations/:id/tasks/:taskId/scan` →
  confirm qty → `POST /stations/:id/tasks/:taskId/complete`

---

## ERP integration

- ERP pushes orders via `POST /orders` (erp_service role)
- WMS calls back ERP on order status changes via `POST {ERP_API_URL}/webhooks/wms-status`
- Inbound orders: type `inbound` — receiving, putaway
- Outbound orders: type `outbound` — pick, pack, dispatch
- ERP sync log stored in `audit_log` with `entity_type = 'erp_sync'`

---

## Error handling conventions

- All unhandled errors caught by Express error middleware — never let a 500 leak a stack trace to the client in production
- Validation: use `zod` on all request bodies; return `400` with field-level errors
- Not found: `404 { error: { code: 'NOT_FOUND', message: '...' } }`
- State machine violations: `409 { error: { code: 'INVALID_TRANSITION', ... } }`
- Auth failures: `401` (missing/invalid token), `403` (insufficient role)

---

## Testing strategy

- **Unit:** state machine helpers, priority scorer, queue depth logic
- **Integration:** full HTTP flow per module using Supertest + test DB + test Redis
- **E2E (key flows):**
  1. ERP posts order → WCS creates tasks → AMR dispatched → operator scans → order completed → ERP callback
  2. Exception raised → supervisor resolves via dashboard → order line updated
- Test DB: separate `wms_test` / `wcs_test` databases; migrations run before suite