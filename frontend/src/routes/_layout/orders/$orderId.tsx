import { createFileRoute, Outlet } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/orders/$orderId")({
  component: Outlet,
})
