import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/commissions/")({
  beforeLoad: () => {
    throw redirect({ to: "/commissions/payments" })
  },
})
