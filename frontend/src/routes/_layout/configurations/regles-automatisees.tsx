import { createFileRoute, redirect } from "@tanstack/react-router"
import { AutomatedRulesView } from "@/components/AutomatedRules/AutomatedRulesView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute(
  "/_layout/configurations/regles-automatisees",
)({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("rules", "manage"))) {
      throw redirect({ to: "/configurations" })
    }
  },
  head: () => ({ meta: [{ title: "Règles automatisées - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Règles automatisées
        </h1>
        <p className="text-muted-foreground">
          Gérer les règles de cohérence et les règles réflexes
        </p>
      </div>
      <AutomatedRulesView />
    </div>
  )
}
