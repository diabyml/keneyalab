import { createFileRoute, redirect } from "@tanstack/react-router"

import { DoctorDetailView } from "@/components/Doctors/DoctorDetailView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/doctors/$doctorId")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("doctors", "view"))) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({ meta: [{ title: "Dossier médecin - KeneyaLab" }] }),
})

function RouteComponent() {
  const { doctorId } = Route.useParams()
  return <DoctorDetailView doctorId={doctorId} />
}
