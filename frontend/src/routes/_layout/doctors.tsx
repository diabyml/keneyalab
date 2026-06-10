import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"

import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/doctors")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("doctors", "view"))) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({ meta: [{ title: "Médecins - KeneyaLab" }] }),
})

function RouteComponent() {
  return <Outlet />
}
