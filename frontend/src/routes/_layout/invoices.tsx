import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"

import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/invoices")({
  component: Outlet,
  beforeLoad: async () => {
    if (!(await ensurePermission("invoices", "view"))) {
      throw redirect({ to: "/" })
    }
  },
})
