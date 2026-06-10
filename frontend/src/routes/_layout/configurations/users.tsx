import { createFileRoute, redirect } from "@tanstack/react-router"

import UsersView from "@/components/Users/UsersView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/users")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("users", "manage"))) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Utilisateurs - KeneyaLab",
      },
    ],
  }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Utilisateurs</h1>
        <p className="text-muted-foreground">
          Gérer les comptes utilisateurs et l&apos;assignation des rôles
        </p>
      </div>
      <UsersView />
    </div>
  )
}
