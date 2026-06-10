import { createFileRoute, redirect } from "@tanstack/react-router"

import { PatientDetailView } from "@/components/Patients/PatientDetailView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/patients/$patientId")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("patients", "view"))) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({ meta: [{ title: "Dossier patient - KeneyaLab" }] }),
})

function RouteComponent() {
  const { patientId } = Route.useParams()
  return <PatientDetailView patientId={patientId} />
}
