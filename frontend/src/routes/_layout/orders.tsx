import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"

import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/orders")({
  component: Outlet,
  beforeLoad: async ({ location }) => {
    const action = location.pathname.endsWith("/new")
      ? "create"
      : location.pathname.endsWith("/edit")
        ? "edit"
        : "view"
    if (!(await ensurePermission("orders", action))) {
      throw redirect({ to: "/" })
    }
  },
})
