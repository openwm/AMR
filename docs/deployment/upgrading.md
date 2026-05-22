# Upgrading

OpenWM follows a simple upgrade path: pull the new code, rebuild the images, and let the API container run migrations on start.

## Standard upgrade

```bash
# 1. Stop the running stack
docker compose down

# 2. Pull the new code
git pull

# 3. Rebuild and restart — Alembic runs automatically on api startup
docker compose up --build -d

# 4. Watch the api logs to confirm migrations ran cleanly
docker compose logs -f api
```

Look for log lines like:

```
INFO  [alembic.runtime.migration] Running upgrade 0003_outbound -> 0004_auth, auth tables
```

## Before upgrading in a non-demo environment

1. **Back up the database**:
   ```bash
   docker exec openwm-db pg_dump -U openwm -d openwm -F c -f /tmp/pre-upgrade.dump
   docker cp openwm-db:/tmp/pre-upgrade.dump ./pre-upgrade-$(date +%Y%m%d).dump
   ```
2. **Review the changelog / migration list** for breaking changes:
   ```bash
   ls backend/alembic/versions/
   ```
3. **Test the upgrade in a staging environment first** if you have one.

## Rollback

The safest rollback is to restore the pre-upgrade backup (see [Deployment manual § 7](deployment-manual.md)).

You can also roll Alembic back one migration:

```bash
docker exec openwm-api alembic downgrade -1
```

…but downgrades are only safe if the new code revision still understands the old schema. Restoring a backup is recommended for any significant version jump.

## Frequent issues during upgrade

See [troubleshooting.md](troubleshooting.md) for symptoms and fixes; the most common issue is a port conflict from a half-stopped previous stack (`docker compose down` before pulling fixes this).
