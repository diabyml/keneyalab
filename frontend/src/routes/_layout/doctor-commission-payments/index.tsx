import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/doctor-commission-payments/")({
  beforeLoad: () => {
    throw redirect({ to: "/commissions/payments" })
  },
})
