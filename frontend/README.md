# Weekly Growth Journal frontend

TanStack Start, React, and TypeScript interface for weekly reflections, feedback,
commitments, and history. The app uses the Django API through the shared
`GrowthService` in [`src/services/`](src/services/). Mock services remain as
isolated test doubles and are not selected by the application.

## Development and checks

Install [Bun](https://bun.sh/), then run these commands from `frontend/`:

```sh
bun install --frozen-lockfile
bun run dev
```

Open the URL printed by Vite. Start Django at `http://localhost:8000` using the
[repository setup instructions](../README.md). The default API base is `/api`;
Vite proxies those development requests to Django on port 8000.

```sh
bun run test
bun run lint
bun run build
```

`VITE_API_BASE_URL` overrides the API base URL, including the `/api` path. It is
compiled into the browser build, so set it before building for a different API
origin. See the [Render deployment guide](../_docs/render-deployment.md) for
service setup and release verification steps.

## Authentication and rendering

The shared HTTP service attaches the bearer token held in module memory. The
token is cleared on sign-out, expiry, or an API `401`; refreshing the page starts
signed out. Account and journal routes use `ssr: false`, and protected routes
check the browser session before loading. Django enforces authentication and
journal ownership on the server.

## Lovable connection

This frontend remains connected to the [Lovable editor](https://lovable.dev/projects/c61e001d-31fb-4478-8e55-d933d6b117e5).
Preserve published Git history and keep changes pushed to the connected branch
in a working state; see [`AGENTS.md`](AGENTS.md).
