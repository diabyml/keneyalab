import { createFileRoute } from "@tanstack/react-router"

import { DashboardView } from "@/components/Dashboard/DashboardView"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Tableau de bord - KeneyaLab",
      },
    ],
  }),
})

function Dashboard() {
  return <DashboardView />
}
