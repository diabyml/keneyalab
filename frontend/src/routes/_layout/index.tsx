import { createFileRoute } from "@tanstack/react-router"

import useAuth from "@/hooks/useAuth"

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

function DashboardContent() {
  const { user: currentUser } = useAuth()

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Bonjour, {currentUser?.full_name || currentUser?.email}
        </h1>
      </div>
    </div>
  )
}

function Dashboard() {
  return <DashboardContent />
}
