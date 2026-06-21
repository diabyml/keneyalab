import { createFileRoute, redirect } from "@tanstack/react-router"

import { PageHeader } from "@/components/Common/PageHeader"
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
      <PageHeader
        eyebrow="Phase pré-analytique"
        title="Prélèvements"
        description="Organiser la collecte et suivre les tentatives"
      />
      <SpecimensView />
    </div>
  )
}
