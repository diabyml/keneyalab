import { createFileRoute } from "@tanstack/react-router"

import { PageHeader } from "@/components/Common/PageHeader"
import { OrderCreateView } from "@/components/Orders/OrderCreateView"

export const Route = createFileRoute("/_layout/orders/new")({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Nouvelle demande - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Nouvelle réception"
        title="Nouvelle demande"
        description="Patient, examens, prélèvements et règlement"
        backTo="/orders"
      />
      <OrderCreateView />
    </div>
  )
}
