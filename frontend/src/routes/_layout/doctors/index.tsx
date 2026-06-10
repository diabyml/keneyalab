import { createFileRoute } from "@tanstack/react-router"

import { DoctorsView } from "@/components/Doctors/DoctorsView"

export const Route = createFileRoute("/_layout/doctors/")({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Médecins - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Médecins</h1>
        <p className="text-muted-foreground">
          Rechercher, créer et gérer les médecins prescripteurs
        </p>
      </div>
      <DoctorsView />
    </div>
  )
}
