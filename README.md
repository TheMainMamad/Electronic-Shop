# فروشگاه الکترونیک — Persian Electronics E-Commerce Platform

A production-grade, Persian-first, RTL e-commerce platform built as a university project,
engineered to real-world standards rather than as a CRUD demo. FastAPI + async SQLAlchemy
backend, React + TypeScript storefront and admin panel, PostgreSQL, Redis, Celery, ZarinPal
sandbox payments, and a Dockerized deployment behind Nginx.

## Project Overview

Customers browse a Persian electronics catalog, manage a cart, check out through ZarinPal
sandbox, track orders, hold a wallet balance, and open support tickets — all in Persian, RTL,
with light/dark/system themes. Admins manage the catalog, orders, payments, users, tickets,
and view an operational dashboard, in a separately-authorized `/admin` area.

Full architectural rationale, ER diagrams, and the threat model live in
[`docs/architecture.md`](docs/architecture.md). Deeper topic docs are in [`docs/`](docs/).

## Architecture

Modular monolith: one FastAPI service, one Postgres database, Redis for cache + Celery
broker, Celery worker/beat for background jobs, Nginx as the sole public entrypoint in front
of the backend and the built frontend. See [`docs/architecture.md`](docs/architecture.md) for
the full breakdown (layering, ER diagram, payment/wallet/cart sequence diagrams, indexes,
concurrency strategy, RBAC model, Git workflow).

## Features

- Persian-first, RTL-native storefront and admin panel, light/dark/system theme
- Local auth (Argon2id, rotating JWT refresh tokens in HttpOnly cookies) + Google OAuth2/OIDC
- RBAC (`customer`/`support`/`admin`/`super_admin`) with object-level authorization
- Dynamic, arbitrarily-nested category tree with cycle protection
- Product catalog with JSONB specifications, Persian-aware search, pagination/filtering
- Concurrency-safe inventory (reserve → commit/release under row locks)
- Cart with server-recomputed pricing, checkout with reservation-backed idempotent orders
- ZarinPal sandbox payments with replay-safe, idempotent verification
- Ledger-style wallet (deposit/purchase/refund/admin adjustment)
- Ticketing with Celery-driven 24h auto-close and full audit trail
- Redis caching with explicit, targeted invalidation (no `KEYS *`)
- Admin dashboard with real aggregated stats and charts
- Idempotency-Key support on all money-moving endpoints

## Technology Stack

**Backend:** Python 3.13, FastAPI, SQLAlchemy 2.x (async), PostgreSQL, Alembic, Pydantic v2,
Redis, Celery + Celery Beat, PyJWT, Argon2id, httpx, structlog, pytest.
**Frontend:** React, TypeScript, Vite, React Router, TanStack Query, Zustand, Tailwind CSS.
**Infrastructure:** Docker, Docker Compose, Nginx.

## Repository Structure

See [`docs/architecture.md#2-repository-tree`](docs/architecture.md).

## Requirements

- Docker + Docker Compose v2
- Node.js 22+ and Python 3.13+ (only needed for running lint/tests outside containers)

## Environment Variables

Copy `.env.example` to `.env` and fill in real values (never commit `.env`). See the file for
the full list: database/Redis credentials, JWT/CSRF secrets, CORS origins, Google OAuth
credentials, ZarinPal sandbox credentials, and seed admin/customer credentials. Generate
secrets with `openssl rand -hex 32` — never use `password`, `admin`, `123456`, `secret`, or
`changeme` as real values.

## Development Setup

```bash
cp .env.example .env        # fill in real values
make up                     # builds and starts the full stack
make migrate                # applies Alembic migrations
make seed                   # loads demo data (Phase 11)
make logs                   # tail logs
make down                   # stop everything
```

The app is served entirely through Nginx at `http://localhost` — the frontend at `/` and the
API at `/api/v1/*`. `docker-compose.override.yml` is auto-loaded locally for hot-reload; it is
not present on the production server.

## Docker Setup

Seven services: `nginx`, `frontend`, `backend`, `postgres`, `redis`, `celery-worker`,
`celery-beat`. Only `nginx` is published on the host. `postgres` and `redis` sit on an
`internal: true` Docker network and are unreachable from outside the Compose stack.

## Database Migrations

```bash
make migration m="add products table"   # autogenerate a revision
make migrate                            # apply pending migrations
```
`Base.metadata.create_all()` is never used as the schema mechanism — Alembic is authoritative
from the first migration onward.

## Seed Data

`make seed` runs an idempotent seed script (admin user, customer user, category tree, 25
products, sample orders/payments/wallet activity, one realistic support ticket). Running it
repeatedly does not duplicate core records. Details in [`docs/database.md`](docs/database.md).

## Google OAuth Setup

Create OAuth 2.0 credentials in Google Cloud Console, set the authorized redirect URI to
`<your-origin>/api/v1/auth/google/callback`, and put the client ID/secret in `.env`. If left
blank, Google login is cleanly disabled rather than broken — see
[`docs/authentication.md`](docs/authentication.md).

## ZarinPal Sandbox Setup

Register at zarinpal.com sandbox, put the merchant ID in `.env` as `ZARINPAL_MERCHANT_ID`
with `ZARINPAL_SANDBOX=true`. Details in [`docs/payments.md`](docs/payments.md).

## Celery

`celery-worker` processes background jobs; `celery-beat` schedules the periodic ticket
auto-close job (every 10 minutes) against Redis DB 1. See
[`docs/background-jobs.md`](docs/background-jobs.md).

## Redis Caching

Cache-aside with versioned, enumerable keys and explicit invalidation. Details in
[`docs/caching.md`](docs/caching.md).

## Authentication

Argon2id password hashing, rotating JWT refresh tokens delivered as `HttpOnly`/`Secure`/
`SameSite=Lax` cookies, double-submit CSRF token on mutating requests. Full flow in
[`docs/authentication.md`](docs/authentication.md) and RBAC model in
[`docs/authorization.md`](docs/authorization.md).

## Admin Panel

Separate `/admin` frontend route tree, backed by the same RBAC — the URL is not the security
boundary, every admin API independently enforces role + permission + audit logging.

## Testing

```bash
make test     # backend pytest + frontend typecheck/lint
make lint     # ruff + mypy + eslint + tsc
```

## Security Architecture

See [`docs/security.md`](docs/security.md) and §19 of
[`docs/architecture.md`](docs/architecture.md) for the full threat model and controls
(IDOR/BOLA, CSRF, mass assignment, upload validation, rate limiting, replay/duplicate
payment protection, race-condition locking).

## Deployment

See [`docs/deployment.md`](docs/deployment.md) and `scripts/deploy.sh` / `make deploy`.

## Git Workflow

Git Flow: `master` (stable/deployable) + `develop` (integration), short-lived
`feature/*`/`bugfix/*`/`refactor/*`/`chore/*`/`security/*` branches, `release/*` branches
tagged into `master`, `hotfix/*` branches from `master` merged back into both. Details in
[`docs/git-workflow.md`](docs/git-workflow.md).

## Troubleshooting

- **Containers unhealthy on first boot:** `make logs` — usually Postgres still initializing;
  `depends_on: condition: service_healthy` should handle ordering automatically.
- **401s from the frontend:** cookies are `SameSite=Lax`; confirm frontend and API are served
  from the same origin through Nginx rather than hitting the backend container directly.
- **Alembic can't connect:** confirm `.env` `POSTGRES_*` values match what the `backend`
  container was started with.

## Production Considerations

Non-root containers, pinned base images, multi-stage builds, health checks, Postgres/Redis
never exposed publicly, Nginx rate limiting + security headers, secrets only via environment
variables, no `allow_origins=["*"]` with credentials, Swagger disabled via `OPENAPI_ENABLED`
where appropriate.
