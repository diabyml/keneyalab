import { createFileRoute } from "@tanstack/react-router"

import { OrderCreateView } from "@/components/Orders/OrderCreateView"

export const Route = createFileRoute("/_layout/orders/$orderId/edit")({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Modifier la demande - KeneyaLab" }] }),
})

function RouteComponent() {
  const { orderId } = Route.useParams()
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Modifier la demande</h1>
        <p className="text-muted-foreground">
          Chaque correction crée une révision auditée sans supprimer
          l'historique clinique ou financier.
        </p>
      </div>
      <OrderCreateView orderId={orderId} />
    </div>
  )
}
