import { createFileRoute } from "@tanstack/react-router"

import ConfigLinks from "@/components/Configurations/ConfigLinks"

export const Route = createFileRoute("/_layout/configurations/")({
  component: RouteComponent,
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Configurations</h1>
        <p className="text-muted-foreground">
          Gérer les paramètres système et le contrôle d'accès
        </p>
      </div>
      <ConfigLinks />
    </div>
  )
}
