import { createFileRoute, redirect } from "@tanstack/react-router"
import { CatalogueView } from "@/components/Catalogue/CatalogueView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/catalogue")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("catalog", "manage"))) {
      throw redirect({ to: "/configurations" })
    }
  },
  head: () => ({ meta: [{ title: "Catalogue - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Catalogue</h1>
        <p className="text-muted-foreground">
          Gérer les tests, panels, prélèvements et tarifs
        </p>
      </div>
      <CatalogueView />
    </div>
  )
}
