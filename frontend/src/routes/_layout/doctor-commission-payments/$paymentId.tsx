import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute(
  "/_layout/doctor-commission-payments/$paymentId",
)({
  beforeLoad: ({ params }) => {
    throw redirect({
      to: "/commissions/payments/$paymentId",
      params: { paymentId: params.paymentId },
    })
  },
})
