# Private deployment preparation

This document is a preparation guide. Render deployment configuration exists,
but no hosted service, database, private-access service, or live endpoint has
been provisioned by this work. Render Free web services are public; CORS is not
an access-control mechanism. Before using a Render Free deployment, keep
account-level authentication enabled and verify the exact frontend origin and
preflight request. For private network access, use a paid/private hosting
configuration or an identity-aware gateway.

## Production settings

Use a private secret manager for every environment-specific value. For
production, configure:

| Setting | Production requirement |
| --- | --- |
| `APP_ENV` | `production` |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_SECRET_KEY` | Unique, randomly generated Django key; do not use the local example value. |
| `TOKEN_SIGNING_KEY` | A separate unique random key; never reuse the Django key. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated API hostnames only; do not use `*`. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated exact HTTPS frontend origins, such as `https://journal.private.example`. Do not include paths, trailing slashes, wildcards, or non-HTTPS URLs. |
| `DATABASE_URL` | PostgreSQL connection with database name, username, password, and private host. Require TLS (`sslmode=require`, `verify-ca`, or `verify-full`). If using individual `POSTGRES_*` settings, set `POSTGRES_SSLMODE` to one of those values. |
| `AI_API_KEY` | Optional. Keep unset until a provider is deliberately configured. |
| `AI_BASE_URL`, `AI_MODEL` | Optional provider routing settings. These do not authorize provider use without an API key. |

The deployment check is available through Django's deployment checks:

```sh
uv run python manage.py check --deploy
```

Run it with the production environment variables loaded from the private secret
manager. The check reports setting names and safe categories only; it must not
print secret values. Test the same check against a valid staging configuration
before promoting a release. `APP_ENV=production` does not itself provision a
database or make the service private.

### Private-access and origin checklist

- Keep the frontend and API behind an identity-aware private access gateway or
  equivalent allowlist. Restrict access to the intended user accounts and
  require multi-factor authentication where the gateway supports it.
- Serve both origins over HTTPS. Restrict API hostnames, network ingress, and
  database access to the required services.
- Keep database credentials, Django/token signing keys, and any future AI key
  in the secret manager. Do not place them in frontend variables, logs, build
  output, or this repository.
- Confirm registration and all journal endpoints are reachable only through
  the private access path. Review the gateway and provider access logs without
  recording reflection content, tokens, or credentials.
- Confirm `APP_ENV=production`, `DJANGO_DEBUG=false`, distinct signing keys,
  a PostgreSQL connection, and an explicit non-wildcard host allowlist with
  `check --deploy` before a release.
- Keep `AI_API_KEY` blank when the optional provider is not intentionally
  enabled. Application startup does not require it.

### Separate-origin CORS

The backend uses `django-cors-headers` and requires `CORS_ALLOWED_ORIGINS` in
production. Supply only exact HTTPS origin URLs (scheme and host, with an
optional port), comma-separated and without a path or trailing slash. The
production deployment check rejects empty, wildcard, non-HTTPS, or malformed
entries. CORS allows only `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, and `OPTIONS`, with
the `Authorization` and `Content-Type` request headers. Cookie credentials are
disabled. Local Vite development proxies `/api` to Django and needs no CORS
allowlist. Verify the actual frontend origin and a preflight request in the
private staging environment before release.

## PostgreSQL backup and restore

Use both the managed PostgreSQL provider's encrypted automated backups and a
periodic encrypted logical backup. Set `DATABASE_URL` through the deployment's
secret injection so the command does not place the connection string in shell
history. Do not echo the variable or include it in logs.

Create a custom-format logical backup:

```sh
pg_dump --format=custom --no-owner --no-privileges \
  --dbname="$DATABASE_URL" \
  --file="weekly-growth-$(date -u +%Y%m%dT%H%M%SZ).dump"
```

Encrypt the file before it leaves the trusted backup host or is copied to
object storage. Store the decryption material separately in the secret
manager. Keep backup storage private, encrypted at rest and in transit, and
limit access to the operator responsible for recovery. A reasonable starting
retention policy is seven daily backups and four weekly backups; set shorter
retention if product or provider requirements demand it, and delete expired
copies from every storage location.

Restore into a new, isolated PostgreSQL database first. Do not test recovery by
overwriting the live database. After decrypting the selected backup, use a
separate `RESTORE_DATABASE_URL` secret:

```sh
pg_restore --no-owner --no-privileges \
  --dbname="$RESTORE_DATABASE_URL" \
  ./weekly-growth-restore-test.dump
```

Point a non-public staging instance at that restored database and verify the
schema and application checks without displaying personal data:

```sh
DATABASE_URL="$RESTORE_DATABASE_URL" uv run python manage.py check --deploy
DATABASE_URL="$RESTORE_DATABASE_URL" uv run python manage.py migrate --check
```

Verify that expected migrations are applied, the health endpoint responds
through the private path, and an authorized test account can retrieve its own
restored review/report/commitment while another test account cannot. Record
the backup timestamp, restore duration, verification result, and safe error
category; do not record reflection bodies or credentials. Destroy the isolated
restore database and temporary plaintext backup after verification according
to the retention policy.
