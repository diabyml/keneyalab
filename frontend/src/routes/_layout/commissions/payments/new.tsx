import { createFileRoute, redirect } from "@tanstack/react-router"

import { PaymentCreateView } from "@/components/DoctorCommissionPayments/PaymentCreateView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/commissions/payments/new")({
  component: PaymentCreateView,
  beforeLoad: async () => {
    if (!(await ensurePermission("commissions", "pay"))) {
      throw redirect({ to: "/commissions/payments" })
    }
  },
  head: () => ({
    meta: [{ title: "Nouveau paiement de commissions - KeneyaLab" }],
  }),
})
