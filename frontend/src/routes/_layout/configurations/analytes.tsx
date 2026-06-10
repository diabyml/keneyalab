import { createFileRoute, redirect } from "@tanstack/react-router"
import { AnalytesView } from "@/components/Analytes/AnalytesView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/analytes")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("catalog", "manage"))) {
      throw redirect({ to: "/configurations" })
    }
  },
  head: () => ({ meta: [{ title: "Analytes - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytes</h1>
        <p className="text-muted-foreground">
          Gérer les analytes, types de résultat et formules
        </p>
      </div>
      <AnalytesView />
    </div>
  )
}
