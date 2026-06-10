import { createFileRoute, redirect } from "@tanstack/react-router"

import PermissionsView from "@/components/Permissions/PermissionsView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/permissions")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("roles", "manage"))) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Permissions - KeneyaLab",
      },
    ],
  }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Permissions</h1>
        <p className="text-muted-foreground">
          Consulter les permissions disponibles dans le système
        </p>
      </div>
      <PermissionsView />
    </div>
  )
}
