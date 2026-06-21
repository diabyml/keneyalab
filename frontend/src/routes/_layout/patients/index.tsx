import { createFileRoute } from "@tanstack/react-router"

import { PageHeader } from "@/components/Common/PageHeader"
import { PatientsView } from "@/components/Patients/PatientsView"

export const Route = createFileRoute("/_layout/patients/")({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Patients - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        eyebrow="Dossiers cliniques"
        title="Patients"
        description="Rechercher, créer et gérer les dossiers patients"
      />
      <PatientsView />
    </div>
  )
}
