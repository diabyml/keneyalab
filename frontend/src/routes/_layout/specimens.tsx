import { createFileRoute, redirect } from "@tanstack/react-router"

import { SpecimensView } from "@/components/Specimens/SpecimensView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/specimens")({
  component: SpecimensPage,
  beforeLoad: async () => {
    if (!(await ensurePermission("specimens", "view"))) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({ meta: [{ title: "Prélèvements - KeneyaLab" }] }),
})

function SpecimensPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Prélèvements</h1>
        <p className="text-muted-foreground">
          Organiser la collecte et suivre les tentatives
        </p>
      </div>
      <SpecimensView />
    </div>
  )
}
