# Troubleshooting

A list of the issues most commonly hit during install, demo, and upgrade — with the fix.

## Containers won't start

### `bind: address already in use` on port 5173 / 8000 / 5432 / 5050

Something on your host is already using one of OpenWM's default ports.

```bash
# On Linux/macOS:
lsof -i :8000
# On Windows (PowerShell):
Get-NetTCPConnection -LocalPort 8000
```

Fix: stop the conflicting process, **or** change the host-side port in `.env`:

```env
API_PORT=8001   # changes only the host side
```

…and restart: `docker compose up -d`.

### `api` container exits immediately

Check the logs:

```bash
docker compose logs api
```

Common causes:

- **Postgres not healthy yet** — the `depends_on: condition: service_healthy` clause should prevent this; if it still happens, run `docker compose up db -d` first, wait 10 seconds, then `docker compose up api -d`
- **Alembic migration error** — usually means the `pgdata` volume is in an inconsistent state. For a demo, `docker compose down -v && docker compose up --build` is the fastest fix (wipes data)

## Database

### `connection refused` from the API to the DB

Make sure both containers are running and on the same network:

```bash
docker compose ps
docker network inspect openwm_default
```

Both `openwm-api` and `openwm-db` should appear under that network.

### "Database already populated — skipping" but the dashboard is empty

This means the seeder ran previously but the data has been removed (or you're looking at the wrong DB). Reset:

```bash
docker compose down -v
docker compose up --build
```

### Need to wipe and re-seed without rebuilding

```bash
docker compose down -v
docker compose up -d
```

## Frontend

### Blank page at http://localhost:5173

Check the dev server logs:

```bash
docker compose logs web
```

If you see "EACCES" or "Cannot find module" errors after pulling new code, the bind-mounted `node_modules` is stale. Rebuild:

```bash
docker compose build web --no-cache
docker compose up -d web
```

### API calls return CORS errors

`CORS_ORIGINS` in `.env` does not include the origin you're using. Add it (comma-separated, no spaces) and `docker compose up -d api` to pick up the change.

### Hot reload not working on Windows

Add a polling-based watcher (already set in `vite.config.ts`, but if you've edited it, verify `server.watch.usePolling: true`). Otherwise Vite won't see changes through the WSL2 / Docker volume mount.

## pgAdmin

### Can't connect to the database from pgAdmin

Inside pgAdmin, when registering a new server use:

| Field    | Value          |
|----------|----------------|
| Host     | `db`           |
| Port     | `5432`         |
| Username | `openwm`       |
| Password | `openwm_dev`   |

Note: it's `db` (the docker-compose service name), **not** `localhost`, because pgAdmin runs in the same docker network.

## Performance

### Dashboard feels slow after a long demo

Charts query the entire movement history. For demos that span hours of clicking, totals will keep growing. Reset with `docker compose down -v && docker compose up --build`.

## Still stuck?

Capture the full logs and open an issue:

```bash
docker compose logs > openwm-logs.txt
```
