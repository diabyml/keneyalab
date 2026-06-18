import { createFileRoute, redirect } from "@tanstack/react-router"

import { LabSettingsView } from "@/components/Configurations/LabSettingsView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/laboratoire")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("lab_settings", "manage"))) {
      throw redirect({ to: "/configurations" })
    }
  },
  head: () => ({ meta: [{ title: "Laboratoire - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Laboratoire</h1>
        <p className="text-muted-foreground">
          Configurer l’identité et les coordonnées utilisées sur les documents
        </p>
      </div>
      <LabSettingsView />
    </div>
  )
}
