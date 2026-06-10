import { createFileRoute } from "@tanstack/react-router"

import { PaymentDetailView } from "@/components/DoctorCommissionPayments/PaymentDetailView"

export const Route = createFileRoute(
  "/_layout/commissions/payments/$paymentId",
)({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Détail du paiement - KeneyaLab" }] }),
})

function RouteComponent() {
  const { paymentId } = Route.useParams()
  return <PaymentDetailView paymentId={paymentId} />
}
