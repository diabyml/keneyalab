import { createFileRoute, redirect } from "@tanstack/react-router"
import { ContextsPatientView } from "@/components/ContextsPatient/ContextsPatientView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute(
  "/_layout/configurations/contexts-patient",
)({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("reference_data", "manage")))
      throw redirect({ to: "/configurations" })
  },
  head: () => ({ meta: [{ title: "Contextes patient - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Contextes patient</h1>
        <p className="text-muted-foreground">
          Gérer les contextes patient (À jeun, Post-prandial, etc.)
        </p>
      </div>
      <ContextsPatientView />
    </div>
  )
}
