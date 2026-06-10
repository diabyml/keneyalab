import { createFileRoute } from "@tanstack/react-router"

import { OrdersView } from "@/components/Orders/OrdersView"

export const Route = createFileRoute("/_layout/orders/")({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Demandes - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Demandes</h1>
        <p className="text-muted-foreground">
          Enregistrer et suivre les demandes d'analyses
        </p>
      </div>
      <OrdersView />
    </div>
  )
}
