# Data Model

## Persistence

MongoDB database name defaults to `tripbank`; the connection is configured by `DATABASE_URL`.

## Collections and key fields

- `users`: `_id`, normalized email, password hash, profile fields, theme/notifications, token version, reset-token fields.
- `trips`: `_id`, name, destination, ISO date strings, group size, budget total/currency, status, owner, invite hash/expiry, approved budget and history, version.
- `trip_members`: trip/user pair, role, target amount, joined timestamp, membership status.
- `payment_orders`: local payment order, provider order id, trip/member, amount/currency, state and idempotency key.
- `contributions`: captured contribution keyed by payment order.
- `ledger_entries`: append-only amount entries keyed uniquely by source and type; contribution, reversal, and expense entries drive balances.
- `trip_expenses`: trip expense fields, category, approval status, payer, receipt and timestamps.
- `ai_insights`: generated trip insights and reporting state.
- `webhook_events`: PayPal event ids for duplicate-event prevention.
- `audit_events`: trip-scoped audit history.

## Relationships

Users participate in trips through `trip_members`. Trips own payment orders, contributions, ledger entries, expenses, AI insights, webhook reconciliation, and audit events. Payment orders reference contributions and ledger source ids. The code enforces relationships through string ids and MongoDB indexes rather than ORM foreign keys.

## Transaction boundaries

The application uses individual MongoDB writes and unique indexes for idempotency. The ledger is append-only; corrections are represented as compensating entries. No multi-document transaction boundary is configured in the inspected code.
