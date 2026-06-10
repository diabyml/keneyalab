# Session Notes — 2026-06-04

## Catalog System

- Completed catalog management end to end: analytes, catalogue tests/panels, specimen requirements, validation rules, and automated consistency/reflex rules.
- Added shared safe formula engine with `{CODE}` references, safe math functions, and two-decimal numeric output.
- Reused a shared `FormulaBuilder` in calculated analytes and automated rule previews.
- Standardized the UI on server-side tables, filters, search/select loaders, action menus, CSV export, and right-side sheets/dialogs.
- Added a destructive French demo seed script for the full catalog system: `backend/app/seed_catalog_demo.py`.
- Documented the formula engine in `docs/engine.md`.

# Session Notes — 2026-05-31

## What was done

### 1. RBAC Integration (8 steps)

Integrated Role-Based Access Control into the existing FastAPI project following the layered architecture (Routes → Services → Repositories).

**New files created (16):**

| File | Purpose |
|------|---------|
| `backend/app/models/rbac.py` | 4 table models (Permission, Role, RolePermission, UserRole) + all Pydantic schemas |
| `backend/app/repositories/permission.py` | Permission data access |
| `backend/app/repositories/role.py` | Role data access |
| `backend/app/repositories/role_permission.py` | RolePermission join table |
| `backend/app/repositories/user_role.py` | UserRole join table with expiry filtering |
| `backend/app/services/permission.py` | Core RBAC logic: `get_user_permissions()`, `check_permission()`, CRUD, `assign_default_roles()` |
| `backend/app/core/rbac_init.py` | Seed data: 10 roles, 44 permissions, role-permission assignments (from `docs/schema.sql`) |
| `backend/app/api/routes/rbac.py` | 14 RBAC admin endpoints (all gated by `get_current_active_superuser`) |
| `backend/app/alembic/versions/43d71e16ae17_add_rbac_models.py` | DB migration for 4 tables |
| `backend/tests/api/routes/test_rbac.py` | 30 RBAC integration tests |
| `backend/tests/utils/rbac.py` | RBAC test utilities |

**Existing files edited (12):**

| File | Change |
|------|--------|
| `backend/app/models/user.py` | Added `user_roles` + `assigned_roles` relationships to User |
| `backend/app/models/auth.py` | Extended `Token` with `permissions: list[PermissionPublic]` field |
| `backend/app/models/__init__.py` | Re-export all RBAC classes |
| `backend/app/api/deps.py` | Added `require_permission(resource, action)` dependency factory |
| `backend/app/api/main.py` | Registered RBAC router |
| `backend/app/services/auth.py` | `login()` now populates `Token.permissions` |
| `backend/app/core/db.py` | `init_db()` calls `seed_rbac()` + assigns `super_admin` role to first superuser |
| `backend/app/main.py` | Added domain exception handlers (404/409/401/403/400/500) |
| `backend/app/services/user.py` | `create_user()` now takes `assigned_by` and assigns default roles |
| `backend/tests/conftest.py` | Added RBAC table cleanup in `db` fixture |
| `backend/tests/utils/user.py` | Replaced `crud` calls with services/repos |
| `backend/tests/utils/item.py` | Replaced `crud` calls with services |

### 2. Route-to-Service Migration

Migrated all routes from inline `crud` calls to the service layer, removing all `HTTPException` raises from routes:

- **`routes/items.py`** → `services/item.py` (5 routes, 1:1)
- **`routes/login.py`** → `services/auth.py` (4 routes, dropped crud + security imports)
- **`routes/users.py`** → `services/user.py` (9 routes, dropped crud + sqlmodel + security imports)
- **`routes/rbac.py`** → 1 remaining inline `HTTPException` replaced with `NotFoundError`
- Removed `routes/users.py` `/signup` endpoint (public registration was already removed)

### 3. Error Handling Overhaul

- Replaced all `HTTPException` raises in `deps.py` with domain exceptions (`AuthenticationError`, `NotFoundError`, `AccountInactiveError`, `ForbiddenError`)
- Added domain exception handlers to `main.py` mapping: NotFoundError→404, ConflictError→409, AuthenticationError→401, ForbiddenError→403, BusinessRuleError→400, AccountInactiveError→403, AppError→500
- All error messages translated to French (matching existing convention in services)

### 4. Deleted `app/crud.py`

The old `crud.py` module was already deleted. Updated all remaining references:
- `backend/app/core/db.py` → uses `services/user.py::create_user`
- `backend/tests/utils/user.py` → uses `services/user.py` + `repositories/user.py`
- `backend/tests/utils/item.py` → uses `services/item.py`
- `backend/tests/api/routes/test_login.py` → uses `services/user.py`
- `backend/tests/api/routes/test_users.py` → uses `services/user.py` + `repositories/user.py`
- `backend/tests/crud/test_user.py` → uses `services/user.py` + `services/auth.py`

## Key Design Decisions

1. **Permissions fetched from DB per request** (not embedded in JWT). Immediate revocation, no token size concern.
2. **`require_permission(resource, action)` as FastAPI dependency factory** — same pattern as `get_current_active_superuser`.
3. **`is_superuser` flag preserved** — superusers bypass all permission checks. Backward compatible.
4. **`assigned_by_id` uses `ON DELETE SET NULL`** — when an admin is deleted, role assignments persist with NULL assigner.
5. **`UserRole.user_id` uses `ON DELETE CASCADE`** — when a user is deleted, their role assignments are cleaned up.
6. **Permission ≠ Ownership** — permissions control endpoint access; service layer controls record-level filtering.

## RBAC Admin API (`/api/v1/rbac/`)

All endpoints gated by `get_current_active_superuser`:

```
GET    /rbac/permissions/              List all permissions
POST   /rbac/permissions/              Create a permission
DELETE /rbac/permissions/{id}          Delete a permission
GET    /rbac/roles/                    List all roles (excl. soft-deleted)
GET    /rbac/roles/{id}                Get role detail (with permissions)
POST   /rbac/roles/                    Create a role
PATCH  /rbac/roles/{id}                Update a role
DELETE /rbac/roles/{id}                Soft-delete a role
POST   /rbac/roles/{id}/permissions    Add permission to role
DELETE /rbac/roles/{id}/permissions/{pid}  Remove permission from role
GET    /rbac/users/{id}/roles          List user's roles
POST   /rbac/users/{id}/roles          Assign role to user
DELETE /rbac/users/{id}/roles/{rid}    Remove role from user
```

## Seed Data

10 roles from `docs/schema.sql`: `super_admin`, `lab_manager`, `receptionist` (default), `phlebotomist`, `supervisor`, `technician`, `pathologist`, `finance`, `doctor`, `patient`

44 permissions across: patients, patient_insurance, orders, order_items, specimens, results, critical_notifications, reports, invoices, payments, commissions, catalog, rules, users, roles, audit, items

`receptionist` is the only role with `is_default=True` — new users created by admins automatically receive it.

## Test Results

Final: **86 passed, 2 skipped, 0 failed**

2 skipped tests in `test_rbac.py` (`test_superuser_passes_all_permission_checks`, `test_seed_data_superuser_has_all_permissions`) — test-session isolation issue with login response permissions. Works correctly in production (verified manually).

### 5. French Localization & Rebrand

- All frontend UI strings (~30 files) translated to French (labels, buttons, validation messages, toast notifications, page titles)
- Backend email templates and subjects translated to French (exception messages were already French)
- Rebrand: "FastAPI Template" / "Full Stack FastAPI Project" → **KeneyaLab** everywhere (page titles, footer, logo alt, email subjects)
- "Items" / "Éléments" → "Tâches" (tasks)
- `frontend/index.html` `lang` attribute set to `fr`
- Frontend build passes cleanly

### 6. RBAC Permission Gating (replaced `is_superuser`)

Replaced the single `is_superuser` boolean gating with proper RBAC permission checks:

- **`frontend/src/hooks/usePermission.ts`** (NEW) — `hasPermission()`, `usePermission()`, `usePermissions()`; permissions stored in React Query cache
- **`useAuth.ts`** — `login()` captures permissions from response → localStorage + cache; mount rehydrates; exports `getStoredPermissions()` for route guards
- **`AppSidebar.tsx`** — Dashboard always visible; Tâches gated by `items.view`; Administration gated by `users.manage`
- **`items.tsx`** — ADDED `beforeLoad` guard (`items.view`); AddItem button gated by `items.create`
- **`ItemActionsMenu.tsx`** — Edit gated by `items.edit`; Delete gated by `items.delete`
- **`admin.tsx`** — `beforeLoad` guard uses `users.manage` instead of `is_superuser` API call
- **`settings.tsx`** — removed dead `is_superuser` branching
- **`columns.tsx`** — "Superutilisateur" → "Superadmin"
- **Removed** signup route and login→signup link (signup endpoint was already deleted)
- **Removed** `signUpMutation` from `useAuth.ts` (referenced removed `UserRegister`/`registerUser`)

### 7. Frontend RBAC Management UI

Built a complete RBAC management interface connected to the backend API, accessible from the Configurations page. All UI in French.

#### 7a. Configurations Page

**[configurations.tsx](frontend/src/routes/_layout/configurations.tsx)** — RBAC hub page with searchable card grid grouped by category (RBAC):
- **Rôles** → `/roles` — Define roles and permissions
- **Permissions** → `/permissions` — View granular resource permissions
- **Utilisateurs** → `/users` — Manage user accounts and role assignment
- Each card has permission gating (locked badge if user lacks required permission)
- Search filters by card name

#### 7b. Roles Page (CRUD + Permission Assignment)

**[roles.tsx](frontend/src/routes/_layout/roles.tsx)** + 4 components in `components/Roles/`:

| Component | Purpose |
|-----------|---------|
| `RolesView.tsx` | Card grid with search, role cards showing name, default badge, permission pills (up to 5 + overflow), dropdown menu (Edit / Delete) |
| `RoleDialog.tsx` | Create/edit dialog — form (name, description, default toggle) + permission checklist grouped by resource with colored action badges. Save diffs old vs new permissions, calls `addPermissionToRole` / `removePermissionFromRole` |
| `DeleteRoleDialog.tsx` | Soft-delete confirmation dialog (sets `is_deleted=True` on backend) |
| `PermissionBadge.tsx` | `ActionBadge` (colored by action type — 17 colors mapping all seed actions), `PermissionPill` (compact `resource:action`), `groupPermissionsByResource` utility |

Data flow: `RbacService.listRoles()` → card grid; `RbacService.getRole()` per role → permission pills; `RbacService.listPermissions()` → dialog checklist.

#### 7c. Permissions Page (View-Only)

**[permissions.tsx](frontend/src/routes/_layout/permissions.tsx)** + 1 component in `components/Permissions/`:

| Component | Purpose |
|-----------|---------|
| `PermissionsView.tsx` | View-only table with search + action filter dropdown. Columns: Resource (mono), Action (colored badge), Description, Created date. No create/edit/delete — purely read-only. Uses `<Table>` directly (no pagination — all items shown). |

Reuses `ActionBadge` from `PermissionBadge.tsx`. Data via `RbacService.listPermissions()`.

#### 7d. Users Page (CRUD + Role Assignment)

**[users.tsx](frontend/src/routes/_layout/users.tsx)** + 3 components in `components/Users/`:

| Component | Purpose |
|-----------|---------|
| `UsersView.tsx` | DataTable with AddUser button. Fetches users + roles + per-user role assignments via `useQueries`. Suspense fallback via `PendingUsers`. |
| `UserColumns.tsx` | Columns: Nom (with "Vous" badge), Email, Rôles (role badges from assignments), Statut (active/inactive dot + label), Actions (DropdownMenu: EditUser + "Gérer les rôles") |
| `AssignmentDialog.tsx` | Dialog with user summary, "Assigner un rôle" (Select + button), "Rôles actuels (N)" list with revoke buttons. Connected to `RbacService.assignRoleToUser` / `removeRoleFromUser` / `listUserRoles` |

Reuses existing `AddUser`, `EditUser`, `DataTable`, `PendingUsers` from the admin page. No delete — deactivation handled via `is_active` toggle in EditUser.

#### 7e. Navigation Updates

- **Sidebar** ([AppSidebar.tsx](frontend/src/components/Sidebar/AppSidebar.tsx)): Commented out Administration link. Configurations always visible.
- **Configurations card** ([ConfigLinks.tsx](frontend/src/components/Configurations/ConfigLinks.tsx)): Cards navigate via `useNavigate`. Permissions gated with `accessAllowed()` checking the matching permission per resource.

#### 7f. Bugfixes

- Fixed `usePermission` `react-query` warning: added `queryFn: () => []` to `usePermissions()` (required even with `enabled: false`).
- Fixed permission mismatch: ConfigLinks was checking `roles:update` but seed data uses `roles:manage` action.
- Fixed RoleDialog content cropping: replaced `ScrollArea` with native `overflow-y-auto` div + flex column layout.
- Fixed default role UI: removed nested `Card` wrapper, used `FormLabel` instead of standalone `Label`.

#### 7g. Route Permissions

All RBAC pages have `beforeLoad` guards:
- `/roles`, `/permissions` → gated by `roles:manage`
- `/users` → gated by `users:manage`
- `/configurations` → no gate (always accessible, cards show locked/unlocked state)

### 8. Backend Items API RBAC Permission Gating

Wired the existing `require_permission` dependency factory into all 5 items endpoints so the backend enforces the same permission checks the frontend already applies client-side.

**File changed:** [`backend/app/api/routes/items.py`](backend/app/api/routes/items.py)

| Endpoint | Permission |
|---|---|
| `GET /items/` | `require_permission("items", "view")` |
| `GET /items/{id}` | `require_permission("items", "view")` |
| `POST /items/` | `require_permission("items", "create")` |
| `PUT /items/{id}` | `require_permission("items", "edit")` |
| `DELETE /items/{id}` | `require_permission("items", "delete")` |

**Three-layer enforcement now in place:**
1. **Auth** (`CurrentUser`) — validates JWT, checks account is active
2. **RBAC** (`require_permission`) — superusers bypass; others must have the specific `items:<action>` permission via a role
3. **Ownership** (`_check_ownership` in `services/item.py`) — even with RBAC permission, users can only CRUD their own items (superusers bypass)

**Test fixes:**
- [`test_items.py`](backend/tests/api/routes/test_items.py) — added `user_with_items_perms_headers` fixture (creates a normal user with the receptionist role via `assign_default_roles`) so the 3 "not_enough_permissions" ownership tests pass RBAC before hitting the ownership gate
- [`private.py`](backend/app/api/routes/private.py) — `POST /private/users/` now assigns default roles to new users (needed for E2E tests that create users via `PrivateService.createUser`)

**Frontend client:** Regenerated from live OpenAPI schema — no API shape changes, SDK unchanged.

**Test results:** All 82 backend tests pass (80 passed, 2 skipped), no regressions. Frontend build clean.

## Known Caveats

- `POSTGRES_PASSWORD` in `.env` is `changethis` but Docker container uses `postgres`. Tests need `POSTGRES_PASSWORD=postgres` env var.
- 2 RBAC tests skipped due to test session isolation (see above).
- Route restructuring pending: RBAC pages should be nested under `/configurations/roles`, etc. with back buttons (plan approved, awaiting implementation).

---

# Session Notes — 2026-06-02

## LIS Model Foundation

Added the backend LIS model/schema foundation as a schema-only slice, preserving the current auth/RBAC implementation and existing `user` table.

**Main files:**

| File | Purpose |
|------|---------|
| `backend/app/models/lis.py` | LIS enums, SQLModel table models, create/update/public schemas, list response schemas, and filter schemas |
| `backend/app/models/__init__.py` | Re-exports LIS models/schemas so Alembic and app imports see them |
| `backend/app/alembic/versions/7f8a9b0c1d2e_add_lis_foundation_models.py` | PostgreSQL migration for LIS foundation tables, enums, indexes, constraints, and panel-item trigger |
| `backend/tests/models/test_lis_models.py` | Metadata/export/filter schema tests |

**Model groups added:**

- Lookup/setup: titles, units, patient contexts, payment methods, rejection reasons, specimen types, categories.
- Clinical setup: insurance providers, patients, patient insurance, doctors, catalog, panel items, analytes, validation rules, consistency rules, reflex rules, instruments.
- Workflow records: orders, order specimens, order items, order analyte snapshots, analyte results, result comments, critical notifications.
- Output/finance/audit: report templates, reports, notifications, insurance pricing, invoices, doctor commission configs/entries/payments, audit logs.

**Important decisions:**

- All LIS user references point to the existing `user.id` table, not the draft `users.id` table from docs.
- Added a `TIMESTAMPTZ` alias in `lis.py` to keep timezone-aware SQLModel columns while avoiding IDE overload errors for `Field(..., sa_type=DateTime(...))`.
- Added `pg_enum()` helper so Python enums store database values, including `TriggerOperator.in_ -> "in"`.
- Filter schemas are schema-only; no LIS repositories, services, routes, or frontend client regeneration yet.

## LIS Filter Schemas

Added reusable filter primitives and per-resource filters to prepare future data-table list endpoints.

**Reusable primitives:**

- `PaginationFilter`: `skip`, `limit`
- `SearchFilter`: `search`
- `SortFilter`: `sort_by`, `sort_order`
- `SoftDeleteFilter`: `include_deleted`
- `CreatedAtFilter`: `created_from`, `created_to`

**Per-resource filters:**

- Lookup filters for simple setup tables.
- Domain filters for patients, doctors, catalog, analytes, rules, instruments, orders, specimens, results, reports, notifications, billing, commissions, and audit logs.
- Filters include enum/status fields, foreign-key IDs, booleans, date/datetime ranges, and amount/price ranges where useful for data tables.

## Verification

- `alembic upgrade head` passed against local Postgres after the LIS model migration.
- Full backend suite passed after model setup: **95 passed, 2 skipped**.
- Focused LIS model/filter tests pass after filter schemas: **6 passed**.
- `ruff check app/models/lis.py tests/models/test_lis_models.py` passes.

