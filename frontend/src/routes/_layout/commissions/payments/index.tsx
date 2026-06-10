import { createFileRoute } from "@tanstack/react-router"

import { PaymentsListView } from "@/components/DoctorCommissionPayments/PaymentsListView"

export const Route = createFileRoute("/_layout/commissions/payments/")({
  component: PaymentsListView,
  head: () => ({ meta: [{ title: "Paiements commissions - KeneyaLab" }] }),
})
