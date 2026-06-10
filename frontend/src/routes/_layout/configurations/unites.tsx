import { createFileRoute, redirect } from "@tanstack/react-router"
import { UnitesView } from "@/components/Unites/UnitesView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/unites")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("reference_data", "manage"))) {
      throw redirect({ to: "/configurations" })
    }
  },
  head: () => ({ meta: [{ title: "Unités - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Unités</h1>
        <p className="text-muted-foreground">
          Gérer les unités de mesure des analytes
        </p>
      </div>
      <UnitesView />
    </div>
  )
}
