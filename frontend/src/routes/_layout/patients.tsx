import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"

import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/patients")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("patients", "view"))) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({ meta: [{ title: "Patients - KeneyaLab" }] }),
})

function RouteComponent() {
  return <Outlet />
}
