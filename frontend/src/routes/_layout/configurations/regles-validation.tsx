import { createFileRoute, redirect } from "@tanstack/react-router"
import { ValidationRulesView } from "@/components/ValidationRules/ValidationRulesView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute(
  "/_layout/configurations/regles-validation",
)({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("rules", "manage"))) {
      throw redirect({ to: "/configurations" })
    }
  },
  head: () => ({ meta: [{ title: "Règles de validation - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Règles de validation
        </h1>
        <p className="text-muted-foreground">
          Configurer les plages, seuils critiques et delta checks
        </p>
      </div>
      <ValidationRulesView />
    </div>
  )
}
