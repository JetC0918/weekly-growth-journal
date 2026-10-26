FROM oven/bun:1 AS build

WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    NITRO_PRESET=node-server
RUN bun run build

FROM node:22-alpine AS runtime
ENV NODE_ENV=production \
    NITRO_HOST=0.0.0.0 \
    NITRO_PORT=3000
WORKDIR /app
COPY --from=build /app/.output ./.output
EXPOSE 10000
CMD ["sh", "-c", "export NITRO_PORT=\"${PORT:-${NITRO_PORT:-3000}}\"; exec node .output/server/index.mjs"]
