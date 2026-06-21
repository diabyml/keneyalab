import { createFileRoute } from "@tanstack/react-router"

import { PageHeader } from "@/components/Common/PageHeader"
import { DoctorsView } from "@/components/Doctors/DoctorsView"

export const Route = createFileRoute("/_layout/doctors/")({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Médecins - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        eyebrow="Réseau prescripteur"
        title="Médecins"
        description="Rechercher, créer et gérer les médecins prescripteurs"
      />
      <DoctorsView />
    </div>
  )
}
