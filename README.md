# SplitWise AI – TripBank (MVP)

Group travel finance workspace: organizer creates a trip, members join by invite, AI drafts a budget, members contribute through **PayPal Sandbox**, the backend verifies each capture and posts it once to an append-only ledger, and everyone sees the same dashboard, expenses and statement.

Stack: React 19 + Vite + Tailwind + React Router + Axios + Recharts + Lucide · FastAPI + Pydantic + PyMongo · MongoDB Atlas · Gemini REST API · PayPal Orders API/JS SDK · Cloudinary (optional).

## Structure

```
backend/app
  main.py config.py db.py deps.py security.py ratelimit.py errors.py money.py schemas.py utils.py seed.py
  routers/   auth users trips payments webhooks expenses ai statements uploads
  services/  ledger paypal payments gemini budget insights
backend/tests            unit tests (money, capture verification, budget validation)
frontend/src
  pages/     Landing AuthPages Dashboard MyTrips CreateTrip JoinTrip Settings TripLayout TripFund Contributions Expenses AIAssistant Statement
  components/ ui BudgetDraft Layout ProtectedRoute
```

## Credentials you provide

Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env`.

| Variable | Where from |
|---|---|
| `DATABASE_URL`, `DATABASE_NAME` | MongoDB Atlas connection string |
| `JWT_SECRET` | any long random string (`python -c "import secrets;print(secrets.token_urlsafe(48))"`) |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Google AI Studio. Without a key the app falls back to a rule-based budget split and answers |
| `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` | PayPal Developer → Sandbox app |
| `PAYPAL_MERCHANT_ID` | Sandbox **Business** account merchant id (organizer). Enables payee verification |
| `PAYPAL_WEBHOOK_ID` | Webhook registered for your API URL (see below) |
| `CLOUDINARY_*` | Optional, receipt uploads |
| `VITE_PAYPAL_CLIENT_ID` | same client id as above (public) |
| `DEFAULT_CURRENCY` / `VITE_DEFAULT_CURRENCY` | Currency supported by your Sandbox accounts (`USD` is safest) |

Never commit `.env`. Secrets stay on the server except the public PayPal client id.

## Run locally

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
python -m app.seed
pytest -q
```

```bash
cd frontend
npm install
npm run dev
```

API docs: http://localhost:8000/docs · App: http://localhost:5173

`python -m app.seed` creates a labelled demo trip (Goa Escape: 2 paid, 2 partial, 1 pending, 1 approved expense). Login `asha@demo.test` / `Demo@12345`. `--reset` rebuilds it. Docker alternative: `docker compose up` (MongoDB + API).

## PayPal Sandbox setup

1. developer.paypal.com → Apps & Credentials (Sandbox) → create an app; copy client id and secret.
2. Sandbox accounts: one **Business** (organizer merchant, copy its merchant id) and **Personal** buyers.
3. Webhooks: add `https://<your-api>/api/v1/webhooks/paypal` with events `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED`, `PAYMENT.CAPTURE.REFUNDED`, `PAYMENT.CAPTURE.REVERSED`; put the webhook id in `PAYPAL_WEBHOOK_ID`. Locally, expose the API with a tunnel.
4. The capture endpoint works without the webhook; the webhook adds late/duplicate/reversal reconciliation.

Money rules implemented: amounts are integer minor units; a browser return never credits anything; capture is verified (status, exact amount and currency, order id, payee); posting is idempotent (unique order id and unique ledger source/type); corrections are compensating ledger entries.

## Endpoints (`/api/v1`)

auth: register, login, forgot-password, reset-password · users: me (GET/PATCH), me/dashboard · trips: create, list, join, get, patch, invites (rotate/revoke), members target/remove, leave, budget, fund, close, contributions, statement · payments: payment-orders, capture · webhooks/paypal · expenses: create, list, edit draft, approve · ai: budget-plan, ask, insights, report · uploads/signature · health.

Stable error codes include INVITE_EXPIRED, NOT_TRIP_MEMBER, AMOUNT_INVALID, ORDER_NOT_APPROVED, CAPTURE_MISMATCH, DUPLICATE_EVENT, RATE_LIMITED.

## Deploy

Backend on Render (Docker or `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers`), env vars in the dashboard, `APP_ENV=production`, `FRONTEND_ORIGIN=https://<vercel-app>`, health path `/health`. Frontend on Vercel with `VITE_API_BASE_URL=https://<api>/api/v1`; `vercel.json` handles client routing. In Atlas, use a least-privilege user and restrict network access.

## Scope notes

Sandbox only: no custodial wallet, escrow, refunds or payouts. PayPal India does not accept domestic payments for India accounts, so a live INR launch needs an India-enabled provider and legal review. Rate limiting is in-process (use a shared store such as Redis if you run multiple instances). Tokens are short-lived access tokens without a refresh flow. Active-session management is not included.
