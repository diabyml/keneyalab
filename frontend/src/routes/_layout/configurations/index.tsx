import { createFileRoute } from "@tanstack/react-router"

import { PageHeader } from "@/components/Common/PageHeader"
import ConfigLinks from "@/components/Configurations/ConfigLinks"

export const Route = createFileRoute("/_layout/configurations/")({
  component: RouteComponent,
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        eyebrow="Administration"
        title="Configurations"
        description="Gérer les paramètres système et le contrôle d'accès"
      />
      <ConfigLinks />
    </div>
  )
}
