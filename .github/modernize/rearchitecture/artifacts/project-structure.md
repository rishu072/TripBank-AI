# Project Structure

## Classification

Full-stack web application with two deployable modules: a FastAPI backend and a React/Vite single-page frontend.

## Modules and layers

- `backend/app/main.py`: FastAPI application factory/lifespan, middleware, exception handlers, router registration, health checks.
- `backend/app/routers/`: HTTP controller layer for auth, users, trips, payments, webhooks, expenses, AI, statements, and uploads.
- `backend/app/services/`: business/integration layer for ledger calculations, budget allocation, AI, PayPal, and payment workflows.
- `backend/app/db.py`, `config.py`, `security.py`, `deps.py`, `schemas.py`, `utils.py`: persistence, configuration, authentication, dependency guards, validation DTOs, and shared utilities.
- `backend/tests/`: focused unit tests for money parsing, budget validation, and PayPal capture verification.
- `frontend/src/pages/`: route-level UI units for landing/auth, dashboard, trips, funds, expenses, AI, and statements.
- `frontend/src/components/`: shared layout, route protection, budget draft, and UI primitives.
- `frontend/src/api.js`, `auth.jsx`, `hooks.js`, `format.js`: API client, auth state, data hooks, and presentation helpers.

## Entrypoints

- Backend: `backend/app/main.py`, served as `app.main:app` by Uvicorn.
- Frontend: `frontend/index.html` → `frontend/src/main.jsx` → `frontend/src/App.jsx`, served by Vite.
- Optional local orchestration: `docker-compose.yml` starts MongoDB and the backend.

## Functional areas

Authentication and password reset; user profile/dashboard; trip creation, invitations, membership and lifecycle; AI budget planning and insights; PayPal Sandbox contributions and webhook reconciliation; expense approval; append-only ledger and statements; optional receipt uploads.
