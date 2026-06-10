import { createFileRoute, redirect } from "@tanstack/react-router"

import { FinanceSettingsView } from "@/components/Configurations/FinanceSettingsView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/finance")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("finance", "manage"))) {
      throw redirect({ to: "/configurations" })
    }
  },
  head: () => ({ meta: [{ title: "Finance - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Finance</h1>
        <p className="text-muted-foreground">
          Configurer les règles financières globales du laboratoire
        </p>
      </div>
      <FinanceSettingsView />
    </div>
  )
}
