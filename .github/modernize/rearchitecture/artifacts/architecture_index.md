# Architecture Index

This index is not the full contract. Do not implement from this file alone; follow the artifact paths below.

## Global artifacts

- `unit_graph.yaml`: entrypoints, dependencies, public contracts, and shared references.
- `wire_contracts.yaml`: REST and PayPal contracts; filter by `unit`.
- `shared_modules.yaml`: shared code and field whitelist; filter by `used_by_units`.
- `cross_unit_state.yaml`: token and browser state flows; filter by writer/reader unit.
- `migration_boundary.yaml`: current analysis scope; `must_rewrite` is empty because this request is analysis-only.
- `project-structure.md`, `tech-stack.md`, `data-model.md`: global structure, stack, and persistence evidence.

## Implementation Guide

For each unit below, read its `behavior.yaml`, `bindings.yaml`, and `unit_decomposition.yaml`. Then filter global rows by the unit name. Completion evidence must report artifact paths read, preserved behavior items, unresolved contracts, and test/build/runtime evidence.

### Units

- `auth`: `units/auth/{behavior,bindings,unit_decomposition}.yaml`; trigger is authentication/password-reset HTTP routes.
- `users`: `units/users/{behavior,bindings,unit_decomposition}.yaml`; trigger is profile/dashboard HTTP routes.
- `trips`: `units/trips/{behavior,bindings,unit_decomposition}.yaml`; trigger is trip lifecycle HTTP routes.
- `payments-webhooks`: `units/payments-webhooks/{behavior,bindings,unit_decomposition}.yaml`; trigger is PayPal order/capture/webhook routes.
- `expenses`: `units/expenses/{behavior,bindings,unit_decomposition}.yaml`; trigger is expense CRUD/approval routes.
- `ai`: `units/ai/{behavior,bindings,unit_decomposition}.yaml`; trigger is AI budget/ask/insight routes.
- `statements-uploads`: `units/statements-uploads/{behavior,bindings,unit_decomposition}.yaml`; trigger is statement and upload-signature routes.
- `frontend-spa`: `units/frontend-spa/{behavior,bindings,unit_decomposition}.yaml`; trigger is browser routes from `frontend/src/App.jsx`.
