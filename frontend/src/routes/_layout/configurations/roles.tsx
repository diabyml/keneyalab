import { createFileRoute, redirect } from "@tanstack/react-router"

import RolesView from "@/components/Roles/RolesView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/roles")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("roles", "manage"))) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Rôles - KeneyaLab",
      },
    ],
  }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Rôles</h1>
        <p className="text-muted-foreground">
          Définir les rôles et leurs permissions
        </p>
      </div>
      <RolesView />
    </div>
  )
}
