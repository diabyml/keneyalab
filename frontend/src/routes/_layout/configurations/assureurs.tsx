import { createFileRoute, redirect } from "@tanstack/react-router"
import { AssureursView } from "@/components/Assureurs/AssureursView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/assureurs")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("reference_data", "manage")))
      throw redirect({ to: "/configurations" })
  },
  head: () => ({ meta: [{ title: "Assureurs - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Assureurs</h1>
        <p className="text-muted-foreground">
          Gérer les assureurs (CNAS, AXA, etc.)
        </p>
      </div>
      <AssureursView />
    </div>
  )
}
