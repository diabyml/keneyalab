import { createFileRoute } from "@tanstack/react-router"

import { PatientsView } from "@/components/Patients/PatientsView"

export const Route = createFileRoute("/_layout/patients/")({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Patients - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Patients</h1>
        <p className="text-muted-foreground">
          Rechercher, créer et gérer les dossiers patients
        </p>
      </div>
      <PatientsView />
    </div>
  )
}
