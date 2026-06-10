import { createFileRoute, redirect } from "@tanstack/react-router"

import { InsurancePricingsView } from "@/components/InsurancePricings/InsurancePricingsView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute(
  "/_layout/configurations/tarifs-assurance",
)({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("finance", "manage"))) {
      throw redirect({ to: "/configurations" })
    }
  },
  head: () => ({ meta: [{ title: "Tarifs assurance - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Tarifs assurance</h1>
        <p className="text-muted-foreground">
          Définir les prix des tests par assureur
        </p>
      </div>
      <InsurancePricingsView />
    </div>
  )
}
