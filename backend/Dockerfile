FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend ./backend

EXPOSE 8000

CMD ["sh", "-c", "uv run --no-sync python backend/manage.py migrate && exec uv run --no-sync uvicorn backend.config.asgi:application --host 0.0.0.0 --port 8000"]
