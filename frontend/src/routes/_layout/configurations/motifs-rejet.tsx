import { createFileRoute, redirect } from "@tanstack/react-router"
import { MotifsRejetView } from "@/components/MotifsRejet/MotifsRejetView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/motifs-rejet")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("reference_data", "manage")))
      throw redirect({ to: "/configurations" })
  },
  head: () => ({ meta: [{ title: "Motifs de rejet - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Motifs de rejet</h1>
        <p className="text-muted-foreground">
          Gérer les motifs de rejet d'échantillons
        </p>
      </div>
      <MotifsRejetView />
    </div>
  )
}
