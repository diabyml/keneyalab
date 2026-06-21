import { createFileRoute } from "@tanstack/react-router"

import { PageHeader } from "@/components/Common/PageHeader"
import { OrdersView } from "@/components/Orders/OrdersView"

export const Route = createFileRoute("/_layout/orders/")({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Demandes - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Circuit pré-analytique"
        title="Demandes"
        description="Enregistrer et suivre les demandes d'analyses"
      />
      <OrdersView />
    </div>
  )
}
