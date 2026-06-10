# KeneyaLab Architecture

This document is the front-to-back reference for adding features safely. It is written for engineers and AI agents working in this repository.

## System Overview

KeneyaLab is split into a React frontend and a FastAPI backend.

```text
Frontend route/page/component
  -> generated OpenAPI client
  -> FastAPI route
  -> service business logic
  -> repository database access
  -> SQLModel models and PostgreSQL
```

The backend is the source of truth for security. Frontend guards improve navigation and user experience, but they must never be the only enforcement point.

## Backend Structure

The backend follows this layering:

```text
backend/app/api/routes -> backend/app/services -> backend/app/repositories -> backend/app/models
```

- `backend/app/api/routes`: FastAPI route handlers. Keep these thin: declare dependencies, validate request/response models, call services, and return public models.
- `backend/app/services`: business logic, transactions, authorization details that depend on domain state, ownership checks, and domain exceptions.
- `backend/app/repositories`: pure database access. Do not commit, create sessions, or raise HTTP exceptions here.
- `backend/app/models`: SQLModel database models and public/request schemas.
- `backend/app/core`: settings, DB engine, security helpers, RBAC seed data, and shared dependencies.
- `backend/tests`: API, service, CRUD, and utility tests.

When adding a backend feature, put DB reads/writes in repositories, workflows and enforcement in services, and HTTP wiring in routes.

## Frontend Structure

The frontend uses TanStack Router, TanStack Query, generated OpenAPI services, and shared UI primitives.

```text
frontend/src/routes
frontend/src/components/<Domain>
frontend/src/components/ui
frontend/src/components/Common
frontend/src/hooks
frontend/src/client
frontend/src/lib
frontend/src/utils.ts
frontend/tests
```

- `frontend/src/routes`: route files and page-level guards. Protected app pages live under `frontend/src/routes/_layout`.
- `frontend/src/components/<Domain>`: domain-specific feature components, for example `Users`, `Roles`, `Items`, `Permissions`.
- `frontend/src/components/ui`: shared design-system primitives only. Do not place feature logic here.
- `frontend/src/components/Common`: reusable app-level components such as data tables, pending states, layout fragments, and common wrappers.
- `frontend/src/hooks`: reusable hooks for auth, permissions, toasts, and shared state/data behavior.
- `frontend/src/client`: generated OpenAPI SDK, types, and schemas. Never hand-edit this folder.
- `frontend/src/lib` and `frontend/src/utils.ts`: small shared utilities.
- `frontend/tests`: Playwright end-to-end tests.

## Frontend Feature Structure

Use this structure for new protected app features:

```text
frontend/src/routes/_layout/<feature>.tsx
frontend/src/components/<Feature>/<Feature>View.tsx
frontend/src/components/<Feature>/Add<Thing>.tsx
frontend/src/components/<Feature>/Edit<Thing>.tsx
frontend/src/components/<Feature>/Delete<Thing>.tsx
frontend/src/components/<Feature>/<Thing>ActionsMenu.tsx
frontend/src/components/<Feature>/<Thing>Columns.tsx
```

The route file should be a page shell:

- declare the TanStack route
- run page-level guards in `beforeLoad`
- set page metadata
- render headings and the feature view component

The feature view should own the real screen behavior:

- query data with TanStack Query
- compose tables, dialogs, filters, and actions
- keep query keys scoped by resource, for example `["users"]`, `["roles"]`, `["items"]`
- call generated services from `@/client`

Do not call raw `fetch` or raw axios from feature code. Use generated services such as `UsersService`, `RbacService`, and `ItemsService`.

## Frontend Guards

There are two frontend guard layers:

1. Page access guards
2. Component/action visibility guards

Protected app pages are nested under `_layout`, which redirects unauthenticated users to `/login`.

Permission-protected pages use:

```ts
beforeLoad: async () => {
  if (!(await ensurePermission("resource", "action"))) {
    throw redirect({ to: "/" })
  }
}
```

Use `ensurePermission(resource, action)` in route `beforeLoad` because it fetches fresh permissions from `GET /users/me/permissions`.

Use `usePermission(resource, action)` inside components for buttons, menus, cards, and links:

```tsx
const canCreateItems = usePermission("items", "create")
return canCreateItems ? <AddItem /> : null
```

Frontend guards are not security boundaries. Every protected backend route must still use `CurrentUser`, `require_permission`, superuser checks, ownership checks, or another server-side rule.

## Auth Flow

Login flow:

```text
Login page
  -> LoginService.loginAccessToken
  -> POST /api/v1/login/access-token
  -> auth service verifies password and active account
  -> JWT access token and permissions returned
  -> frontend stores access_token and permissions in localStorage
```

Request flow:

```text
OpenAPI.TOKEN reads localStorage.access_token
  -> generated client sends Authorization: Bearer <token>
  -> get_current_user decodes JWT
  -> user is loaded from DB
  -> inactive accounts are rejected
```

Global frontend error behavior:

- `401` clears `access_token` and `permissions`, then redirects to `/login`.
- `403` does not log the user out. The user remains authenticated and sees the normal permission error path.

## RBAC Flow

RBAC uses permissions as `resource:action` pairs, assigned to roles, assigned to users.

Important backend pieces:

- `backend/app/core/rbac_init.py`: seed permissions, seed roles, and seed role-permission mappings.
- `backend/app/api/deps.py`: `require_permission(resource, action)`.
- `backend/app/services/permission.py`: permission resolution and role/permission management.
- `GET /users/me/permissions`: fresh effective permissions for frontend guards.

Superusers bypass permission checks on the backend. Normal users must receive permissions through active, non-deleted roles.

Current high-level permissions:

- `users:manage`: normal user administration.
- `roles:manage`: RBAC administration, including permissions, roles, role-permission assignment, and user-role assignment.
- `items:view`, `items:create`, `items:edit`, `items:delete`: item CRUD.

`is_superuser` is a platform-level privilege. A normal user with `users:manage` cannot create or promote superusers. The backend enforces this, and the frontend should hide superuser controls from non-superusers.

## Ownership Flow

RBAC answers: "Can this user perform this kind of action?"

Ownership answers: "Can this user perform this action on this specific record?"

Items use both:

```text
items route
  -> require_permission("items", action)
  -> item service
  -> ownership check
```

Normal users can only access their own items. Superusers bypass item ownership checks.

For future resources that are user-owned, repeat this pattern: route-level permission first, service-level ownership second.

## Generated API Client

The frontend client is generated from the backend OpenAPI schema.

Do not edit:

```text
frontend/src/client
frontend/openapi.json
```

Regenerate the client after changing backend API routes, request models, response models, or query parameters.

Typical workflow:

```bash
cd backend && uv run uvicorn app.main:app --port 8000
curl http://localhost:8000/api/v1/openapi.json > frontend/openapi.json
cd frontend && bun run generate-client
```

Then use generated services from `@/client` in frontend code.

## New Feature Checklist

Use this checklist when adding a new feature.

Backend:

- Add or confirm the needed permission seed in `rbac_init.py`.
- Add or update models and public/request schemas.
- Add repository functions for DB access.
- Add service functions for business logic, transactions, domain exceptions, and ownership checks.
- Add route handlers with `CurrentUser` or `require_permission`.
- Add route/service tests for allowed, denied, not-found, conflict, and ownership cases.

Frontend:

- Regenerate the API client if the backend API changed.
- Add a protected route in `frontend/src/routes/_layout/<feature>.tsx`.
- Add a domain view in `frontend/src/components/<Feature>/<Feature>View.tsx`.
- Add sibling domain components for tables, columns, dialogs, and action menus.
- Use generated services from `@/client`.
- Use TanStack Query for queries and mutations.
- Add `ensurePermission` page guards for protected pages.
- Add `usePermission` component guards for buttons, cards, menus, and links.
- Add sidebar or configuration links only if the feature should be navigable.
- Run backend tests and `npm run build`.

## Security Rules

- Never rely on frontend guards only.
- Every protected backend route must use auth and permission dependencies.
- Put record-level ownership and business rules in services.
- Keep routes thin.
- Keep repositories free of commits and authorization logic.
- Never hand-edit generated frontend client files.
- Clear frontend auth state on `401`, not on every `403`.
- Do not add user delete UI unless backend delete endpoints intentionally exist.
- Keep `/private/users/` local-only. It is unauthenticated and must remain mounted only when `ENVIRONMENT == "local"`.

## Local-Only Private API

`POST /private/users/` is intentionally unauthenticated for local and E2E workflows. It is included only when:

```text
settings.ENVIRONMENT == "local"
```

Do not use this endpoint for production user creation. Production user creation goes through `/users/` and `users:manage`.
