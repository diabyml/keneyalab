import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"

import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/results")({
  component: Outlet,
  beforeLoad: async () => {
    if (!(await ensurePermission("results", "view"))) {
      throw redirect({ to: "/" })
    }
  },
})
