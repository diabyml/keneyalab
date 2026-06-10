import { createFileRoute } from "@tanstack/react-router"

import { OrderCreateView } from "@/components/Orders/OrderCreateView"

export const Route = createFileRoute("/_layout/orders/new")({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Nouvelle demande - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Nouvelle demande</h1>
        <p className="text-muted-foreground">
          Patient, examens, prélèvements et règlement
        </p>
      </div>
      <OrderCreateView />
    </div>
  )
}
