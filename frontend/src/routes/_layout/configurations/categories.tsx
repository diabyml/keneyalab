import { createFileRoute, redirect } from "@tanstack/react-router"
import { CategoriesView } from "@/components/Categories/CategoriesView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/categories")({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("catalog", "manage"))) {
      throw redirect({ to: "/configurations" })
    }
  },
  head: () => ({ meta: [{ title: "Catégories - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Catégories</h1>
        <p className="text-muted-foreground">
          Gérer le regroupement et l'ordre d'affichage du catalogue
        </p>
      </div>
      <CategoriesView />
    </div>
  )
}
