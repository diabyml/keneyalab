import { createFileRoute, redirect } from "@tanstack/react-router"
import { MethodesPaiementView } from "@/components/MethodesPaiement/MethodesPaiementView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute(
  "/_layout/configurations/methodes-paiement",
)({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("reference_data", "manage")))
      throw redirect({ to: "/configurations" })
  },
  head: () => ({ meta: [{ title: "Méthodes de paiement - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Méthodes de paiement
        </h1>
        <p className="text-muted-foreground">
          Gérer les méthodes de paiement (Espèces, Carte bancaire, etc.)
        </p>
      </div>
      <MethodesPaiementView />
    </div>
  )
}
