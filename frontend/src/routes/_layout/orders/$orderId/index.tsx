import { createFileRoute } from "@tanstack/react-router"

import { OrderDetailView } from "@/components/Orders/OrderDetailView"

export const Route = createFileRoute("/_layout/orders/$orderId/")({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Détail demande - KeneyaLab" }] }),
})

function RouteComponent() {
  const { orderId } = Route.useParams()
  return <OrderDetailView orderId={orderId} />
}
