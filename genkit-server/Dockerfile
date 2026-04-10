# ── The Inclusive Citizen — Genkit TypeScript Orchestration Server ────────────
# Multi-stage build: compile TypeScript in the builder stage, then copy only
# the compiled JS output to the lean runner stage.

# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM node:20-slim AS builder

WORKDIR /build

# Install ALL dependencies (including devDependencies) so tsc is available.
COPY package.json package-lock.json ./
RUN npm ci

# Copy TypeScript source and compiler config, then compile.
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build
# Output is written to lib/ (configured in tsconfig.json outDir).

# ── Stage 2: runner ───────────────────────────────────────────────────────────
FROM node:20-slim AS runner

WORKDIR /app

# Install only production dependencies in the runner image.
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Copy compiled JS from the builder stage.
# src/, tsconfig.json, and node_modules devDependencies are NOT copied,
# so the final image contains only what is needed to run the server.
COPY --from=builder /build/lib ./lib

# Cloud Run injects PORT=8080; the server reads process.env.PORT.
ENV PORT=8080
EXPOSE 8080

# package.json has "type": "module" and tsconfig targets ESNext, so Node 20
# can run the compiled ES modules directly without any bundler.
CMD ["node", "lib/index.js"]
