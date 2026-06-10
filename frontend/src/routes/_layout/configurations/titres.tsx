import { createFileRoute, redirect } from "@tanstack/react-router"
import { TitresView } from "@/components/Titres/TitresView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/titres")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("reference_data", "manage"))) {
      throw redirect({ to: "/configurations" })
    }
  },
  head: () => ({ meta: [{ title: "Titres - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Titres</h1>
        <p className="text-muted-foreground">
          Gérer les titres de civilité (Dr, Pr, etc.)
        </p>
      </div>
      <TitresView />
    </div>
  )
}
