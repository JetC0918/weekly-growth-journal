# Local observability

The Django API uses OpenTelemetry for request traces and request metrics,
and privacy-safe structured workflow log records. Exports use OTLP to a local
Collector. The Collector sends metrics to Prometheus, logs to Loki, and traces
to Tempo; Grafana has provisioned data sources and a Weekly Growth Journal
dashboard. This follows the OTel Collector and Prometheus/Loki/Tempo/Grafana
pattern in [DevOps and Observability for an AI-Built App](https://aishippingblog.com/p/devops-and-observability-for-an-ai).

## Start the local stack

From the repository root, start the app first. This creates the private Docker
network shared with the separate observability Compose project:

```sh
docker compose up --build -d
docker compose -f observability/docker-compose.yml up -d
```

Enable export for the API by setting this value in `.env`, then recreate the
backend:

```dotenv
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
APP_VERSION=local
```

Open Grafana at `http://localhost:3001`. Use the credentials configured by
`GRAFANA_ADMIN_USER` and `GRAFANA_ADMIN_PASSWORD` in `.env`. The default port is
bound to loopback only. Prometheus, Loki, and Tempo are also bound to loopback
for local diagnostics. The telemetry services have separate Docker volumes;
stop them with `docker compose -f observability/docker-compose.yml down`.
Use `-v` only to remove local telemetry history. Stop the application with
`docker compose down`; its PostgreSQL data is kept separately.

If Django runs directly on the host rather than in Compose, point
`OTEL_EXPORTER_OTLP_ENDPOINT` at `http://localhost:4317` instead.

## Dashboard and journey signals

The provisioned dashboard is filterable by deployment environment and version.
It includes the rate of account registration/login, review save/completion,
follow-up generation, insight updates, commitment saves, and journal deletion;
HTTP p95 latency; recent structured logs; and recent traces. Report generation
is a child span within review completion. Failures use bounded outcome values
such as `provider_failed` and `persistence_failed`, not exception text.

To create local evidence, complete a weekly review using a local test account,
save a commitment, then open the dashboard. The local `fake` provider is the
default and makes no external AI request. Confirm the event counters advance,
open the matching request trace, and use the trace ID to correlate its log
records. This describes a repeatable verification procedure; it is not a claim
that a dashboard walkthrough or deployment has already been performed.

## Privacy and limits

Telemetry attributes are limited to service/environment/version, route and
HTTP status, workflow event, outcome, and OpenTelemetry trace context. Raw URL
paths and query strings are replaced before server spans are exported, while
resolved route templates remain available for grouping. The app does not
intentionally attach usernames, account or review IDs, request bodies,
reflection text, AI prompts/responses, provider errors, or authorization
headers. Do not add those fields to spans or logs. The workflow metric uses
bounded labels and does not identify individual accounts.

This setup is for local development and rubric demonstration. It has no remote
authentication, TLS, backups, alert routing, or production retention controls.
Keep it on a trusted machine. For deployment, use an authenticated OTel-compatible
backend and decide privacy-safe retention before enabling exports.

## Latest local verification attempt

On 2026-10-26, the Docker CLI was available but could not connect to the Docker
Engine named pipe (`npipe:////./pipe/docker_engine`); the command returned
`permission denied`. The observability Compose project could not be started from
this session, so telemetry collection and the correlated dashboard journey
remain unverified here. This environment result does not distinguish a stopped
Docker Desktop service from an access restriction on the named pipe.
