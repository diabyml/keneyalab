# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Identity

Keneya Lab — a Laboratory Information System (LIS) built on the Full Stack FastAPI Template. The project manages patients, orders, specimens, lab results, reports, invoices, and doctor commissions. Error messages and UI labels are in **French**.

## Commands

### Development

```bash
# Full Docker Compose stack (Postgres, backend, frontend, Adminer, MailCatcher)
docker compose watch

# Backend only (local, no Docker)
cd backend && uv sync && source .venv/bin/activate
fastapi dev app/main.py

# Frontend only (local, no Docker)
bun install && bun run dev          # from repo root
```

### Testing

```bash
# Backend tests (full Docker lifecycle)
bash ./scripts/test.sh

# Backend tests (against a running stack, pass pytest args through)
docker compose exec backend bash scripts/tests-start.sh -x

# Single test file
docker compose exec backend bash scripts/tests-start.sh backend/tests/api/routes/test_items.py

# Frontend E2E tests (requires Docker Compose stack running)
docker compose up -d --wait backend
bunx playwright test
bunx playwright test --ui
```

### Linting & Code Quality

```bash
# Run all pre-commit hooks manually
uv run prek run --all-files

# Python: ruff check + format + mypy + ty
uv run ruff check --force-exclude --fix --exit-non-zero-on-fix backend/
uv run ruff format --force-exclude backend/
uv run mypy backend/app
uv run ty check backend/app

# Frontend: biome
bun run lint          # from repo root, or `biome check --write --unsafe ./` in frontend/
```

### Database Migrations

```bash
# Create a new migration after changing models
docker compose exec backend bash
alembic revision --autogenerate -m "Description of change"
alembic upgrade head
```

### Generate Frontend API Client

After backend API changes, regenerate the auto-generated frontend client:

```bash
bash ./scripts/generate-client.sh
```

### Build

```bash
# Frontend production build
cd frontend && bun run build

# Docker images
docker compose -f compose.yml build
```

## Architecture

### Backend Layering (strict)

```
routes → services → repositories → models
```

| Layer | Location | Rules |
|-------|----------|-------|
| **Routes** | `backend/app/api/routes/` | Thin: declare deps, call services, return public schemas. No business logic, no direct DB access. |
| **Services** | `backend/app/services/` | Business logic, transactions, ownership checks, domain exceptions. No HTTP concerns. |
| **Repositories** | `backend/app/repositories/` | Pure DB access (SQLModel queries). No commits, no session creation, no HTTP exceptions. |
| **Models** | `backend/app/models/` | SQLModel table definitions + Pydantic request/response schemas. |

Key backend files:
- [backend/app/main.py](backend/app/main.py) — FastAPI app creation, CORS, domain exception handlers
- [backend/app/api/main.py](backend/app/api/main.py) — router aggregation; private routes only mounted in `local` env
- [backend/app/api/deps.py](backend/app/api/deps.py) — `SessionDep`, `CurrentUser`, `require_permission(resource, action)` dependency factory
- [backend/app/core/config.py](backend/app/core/config.py) — Pydantic settings from `.env`, DB URI construction, secret validation
- [backend/app/core/exceptions.py](backend/app/core/exceptions.py) — domain exception hierarchy (`AppError` → `NotFoundError`, `ConflictError`, `ForbiddenError`, etc.)
- [backend/app/core/rbac_init.py](backend/app/core/rbac_init.py) — seed data: 10 roles, 44 permissions, role-permission mappings
- [backend/app/core/db.py](backend/app/core/db.py) — engine, `init_db()` (creates first superuser, seeds RBAC, assigns super_admin role)

### Frontend Structure

```
routes → components/<Domain> → generated client → backend API
```

- `frontend/src/routes/` — TanStack Router pages. Protected routes under `_layout/`.
- `frontend/src/components/<Domain>/` — feature components (Users, Roles, Items, Permissions, etc.)
- `frontend/src/components/ui/` — shadcn/ui primitives only; no feature logic
- `frontend/src/client/` — auto-generated OpenAPI SDK, types, schemas (**never hand-edit**)
- `frontend/src/hooks/` — `useAuth`, `usePermission`, `useCustomToast`, `useMobile`
- `frontend/tests/` — Playwright E2E tests

### Feature Component Patterns

Keep feature views as small coordinators, not all-in-one files. `*View.tsx` components should own page-level state, server query parameters, and composition only. Split domain UI into feature-local files for columns, filters, action menus, dialogs/sheets, forms, detail sections, labels, types, and pure helpers. Follow the current `ValidationRules` and `Catalogue` structure when adding or refactoring large management pages.

- Put row actions in `*ActionsMenu.tsx` and gate mutation actions with `usePermission(resource, action)`, even when the route is already guarded.
- Put table columns and CSV export column definitions in `columns.tsx`; use `ServerDataTable` or `SimpleTable` from Common.
- Put create/edit forms in dedicated dialog or sheet components; keep shared form fields in local feature components when reused.
- Put constants, labels, request mappers, formatters, and query-key helpers in local `labels.ts`, `types.ts`, or `utils.ts`.
- Keep all API access through generated client services and React Query; do not call raw `fetch` or axios.

### Data Table Patterns

Two reusable table components exist in `frontend/src/components/Common/`:

- **`ServerDataTable`** — use for every API-backed or growable paginated table. Pagination, sorting, search, and filters must be server-side; parent components own `page`, `pageSize`, `sortBy`, `sortOrder`, and API query state. Do not recreate pagination footers inside feature pages.
- **`SimpleTable`** — use for small, already-loaded, non-paginated datasets. It renders all rows at once and must not be used for growable server datasets.

Both accept `columns: ColumnDef<TData, TValue>[]` and `data: TData[]`, are built on `@tanstack/react-table` with `ui/table` primitives, and support row selection plus CSV export for selected rendered rows. Select-all means the currently rendered rows only, not all matching rows in the database.

`DataTable` was removed. Do not reintroduce client-side pagination for server data.

### Selection Controls

- Use `frontend/src/components/Common/SearchSelect.tsx` for any API-backed or growable option list (roughly more than 10-15 options), such as analytes, units, catalog tests, specimen types, categories, patients, doctors, insurers, or users.
- `SearchSelect` must search server-side. Do not preload long datasets and filter them locally in the browser.
- Use plain `Select` only for short fixed enums such as status, type, gender, yes/no filters, page size, and other small static choices.
- Keep the generated SDK as the only frontend API access path for `SearchSelect` loaders; do not use raw `fetch` or axios.

### LIS Domain Models

The domain model is in [backend/app/models/lis.py](backend/app/models/lis.py) (~1800 lines). It defines the full lab workflow:

**Reference data**: Title, Unit, PatientContext, PaymentMethod, RejectionReason, SpecimenType, Category, InsuranceProvider

**Clinical setup**: Patient, PatientInsurance, Doctor, Catalog (item/panel), CatalogSpecimenRequirement, CatalogPanelItem, Analyte, CatalogItemAnalyte, ValidationRule, ConsistencyRule, ReflexRule, Instrument

**Orders & results**: Order, OrderSpecimen, OrderItem, AnalyteResult, AnalyteResultComment, CriticalNotification

**Reporting & finance**: ReportTemplate, Report, Notification, InsurancePricing, Invoice, DoctorCommissionConfig, DoctorCommissionEntry, DoctorCommissionPayment, AuditLog

Every model follows the pattern: `<Entity>Base` → `<Entity>` (table) / `<Entity>Create` / `<Entity>Update` / `<Entity>Public`.

### RBAC System

Permissions are `resource:action` pairs (e.g., `"patients:create"`, `"results:verify"`). They are assigned to Roles, which are assigned to Users.

- **10 seed roles**: super_admin, lab_manager, receptionist, phlebotomist, supervisor, technician, pathologist, finance, doctor, patient
- **44 seed permissions** covering all LIS resources
- `super_admin` gets ALL permissions at seed time
- Superusers (`is_superuser=True`) bypass all permission checks
- Permissions are fetched from DB per request (not embedded in JWT) for immediate revocation
- Frontend guards: `ensurePermission(resource, action)` in route `beforeLoad`, `usePermission(resource, action)` in components

### Auth Flow

1. Login → JWT access token + permissions returned
2. Requests send `Authorization: Bearer <token>` via generated client
3. `get_current_user` decodes JWT, loads user from DB, rejects inactive accounts
4. Frontend clears auth state on 401 (redirects to `/login`), stays authenticated on 403

### Ownership Pattern

RBAC controls **action** access. Ownership controls **record** access. Both are checked:
1. Route-level: `require_permission("items", "edit")`
2. Service-level: ownership check (normal users can only access their own records; superusers bypass)

## Key Conventions

- **Language**: All user-facing error messages and UI labels are in French
- **IDs**: UUIDs everywhere, generated with `uuid_pk()` factory
- **Timestamps**: `TIMESTAMPTZ` via `utc_timestamp_field()` factory
- **Soft delete**: Most reference/lookup tables use `is_deleted` flag; RBAC roles also soft-deletable
- **Catalog panel pricing**: Panels do not have manual prices. A panel response `price` is computed from attached item/test prices; persisted panel `catalog.price` stays `0.00`. Orders and invoices should bill expanded item rows, not a panel-level price.
- **No `HTTPException`**: Use domain exceptions from `app/core/exceptions.py`; they are mapped to HTTP status codes in `main.py`
- **Server-side search & filter**: All search and filtering operations should be implemented server-side (backend API endpoints with query parameters). The frontend sends the search/filter criteria in the API request, and the backend performs the actual filtering via DB queries. Only use client-side filtering when explicitly stated as an exception for a specific use case (e.g., small fixed datasets already fully loaded)
- **TanStack React Query**: Use `@tanstack/react-query` for server-state caching and cache invalidation. Leverage `useQuery` for fetching data, `useMutation` for mutating data with proper `onSuccess` cache invalidation via `queryClient.invalidateQueries()`. Keep stale times and cache durations appropriate to the data's volatility. Use `queryKeys` consistently to enable targeted invalidation after mutations
- **No raw `fetch`/axios in frontend**: Always use generated services from `@/client`
- **Never edit `frontend/src/client/`** or `frontend/openapi.json` — regenerate from backend OpenAPI schema
- **Pre-commit**: `prek` (not `pre-commit`) runs ruff, ruff-format, biome, mypy, ty, zizmor


## Backend Test Runner Note

When running focused backend tests in Docker, make sure the backend container sees the full `backend/tests` tree, especially `backend/tests/conftest.py`.

During the categories page work, these commands were attempted:

```bash
docker compose exec backend bash scripts/tests-start.sh backend/tests/api/routes/test_categories.py
docker compose exec backend pytest tests/api/routes/test_categories.py
```

Both failed with `fixture 'client' not found` because the running container only had the new category test files mounted (`tests/api/routes/test_categories.py`, `tests/utils/category.py`) and did not have `tests/conftest.py`. The test code itself was not reached. Backend static checks for the new category files passed with:

```bash
docker compose exec backend ruff check app/api/routes/categories.py app/services/category.py app/repositories/category.py tests/api/routes/test_categories.py tests/utils/category.py
python3 -m py_compile backend/app/api/routes/categories.py backend/app/services/category.py backend/app/repositories/category.py backend/tests/api/routes/test_categories.py backend/tests/utils/category.py
```
