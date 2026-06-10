import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/doctor-commission-payments")({
  component: Outlet,
  beforeLoad: async () => {
    if (!(await ensurePermission("commissions", "view"))) {
      throw redirect({ to: "/" })
    }
  },
})
